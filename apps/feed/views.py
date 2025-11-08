from django.shortcuts import render
from apps.scraper.models import Article
from django.http import JsonResponse
from django.shortcuts import redirect

from apps.scraper.translator import translate_to_french
from apps.scraper.translator import translate_to_arabic
from apps.scraper.summarizer import summarize_article_by_id
from apps.recommendations.recommendation import generate_recommendations_for_user  # import your function
from django.contrib.auth.decorators import login_required

# def home(request):
#     try:
#         article = Article.objects.get(id=1)
#     except Article.DoesNotExist:
#         article = None  # Handle the case when it doesn't exist
#     return render(request, 'index.html', {'article': article})

# def home(request):
#     # Fetch last 10 articles ordered by published date
#     articles = Article.objects.order_by('-published_at')[:10]
#     return render(request, 'index.html', {'articles': articles})


@login_required(login_url='/home/Login')
def article_detail(request, pk):  # Changed from 'id' to 'pk'
    """Individual article detail view"""
    article = Article.objects.get(id=pk)  
    context = {
        'article': article
    }
    return render(request, 'index.html', context)
@login_required(login_url='/home/Login')

def home(request):
    return redirect('/latest')

@login_required(login_url='/home/Login')

def recommendation(request):
    user = request.user
    recommendations = []
    # If the user is authenticated, fetch personalized recommendations
    if request.user.is_authenticated:
        user_id = request.user.id
        recommendations = generate_recommendations_for_user(user_id, top_n=10)
        # Add text to each recommendation
    for rec in recommendations:
        try:
            article = Article.objects.get(id=rec['id'])
            rec['text'] = article.text
            rec['source'] = article.source
            rec['scraped_at'] = article.published_at
        except Article.DoesNotExist:
            rec['text'] = "Text not available"

    # Fallback: latest 10 articles
    if not recommendations:
        latest_articles = Article.objects.order_by('-published_at')[:]
        recommendations = [
            {
                "id": a.id,
                "title": a.title,
                "text": a.text,
                "category": a.category,
                "source": a.source,
                "score": None,
                "sentiment": getattr(a, "sentiment", None),
                "scraped_at": a.published_at,
            }
            for a in latest_articles
        ]

    return render(request, 'feed.html', {'articles': recommendations})
@login_required(login_url='/home/Login')

def latest_feed(request):
    """Display latest articles feed based on published date"""
    # Get the latest 10 articles ordered by published date
    latest_articles = Article.objects.order_by('-published_at')[:]
    
    # Format articles as dictionaries (consistent with your feed format)
    articles = [
        {
            "id": article.id,
            "title": article.title,
            "text": article.text,
            "category": article.category,
            "source": article.source,
            "score": None,
            "sentiment": getattr(article, "sentiment", None),
            "scraped_at": article.published_at,
        }
        for article in latest_articles
    ]
    
    return render(request, 'feed.html', {'articles': articles})

@login_required(login_url='/home/Login')

def contact_page(request):
    return render(request, "contact.html")
@login_required(login_url='/home/Login')

def translate_article(request):
    text = request.GET.get('text', '')
    lang = request.GET.get('lang', 'fr')  # default French

    if not text:
        return JsonResponse({'error': 'No text provided'}, status=400)

    if lang == 'ar':
        translated_text = translate_to_arabic(text)
    else:
        translated_text = translate_to_french(text)

    return JsonResponse({'translated_text': translated_text})
@login_required(login_url='/home/Login')
def summarize_article(request):
    article_id = request.GET.get('id')
    if not article_id:
        return JsonResponse({'error': 'No article ID provided'}, status=400)

    summary = summarize_article_by_id(article_id)
    if summary:
        return JsonResponse({'summary': summary})
    return JsonResponse({'error': 'Could not summarize article'}, status=500)


    #------------------------------ Sentiment analysis ---------------------------------------------------
import json
import base64
from io import BytesIO
import torch
import shap
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import re
import nltk
# nltk.data.path.insert(0, '/usr/local/nltk_data')  # <--- INSERT AT FRONT

# from nltk.corpus import stopwords
# EN_STOPWORDS = set(stopwords.words("english"))
# Nothing runs at import time - just defines the function
def get_spacy_stopwords():
    """This function ONLY runs when you call it"""
    import spacy  # ← Import happens HERE, inside function
    nlp = spacy.load("en_core_web_sm")  # ← Only loads when function is called
    return nlp.Defaults.stop_words

_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        try:
            _nlp = spacy.load("en_core_web_sm", disable=["parser", "tagger"])
            print("spaCy model loaded")
        except OSError as e:
            print(f"spaCy model failed: {e}")
            _nlp = None
    return _nlp
MODEL_PATH = "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"
sentiment_model = None
sentiment_tokenizer = None
id2label = {0: "negative", 1: "neutral", 2: "positive"}

# ----------------------------------------------------------------------
# Model loading (lazy)
# ----------------------------------------------------------------------

def load_sentiment_model():
    global sentiment_model, sentiment_tokenizer
    if sentiment_model is None:
        print(f"Loading sentiment model from {MODEL_PATH}...")
        sentiment_tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        sentiment_model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
        sentiment_model.eval()
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        sentiment_model.to(device)
        print(f"Sentiment model loaded on {device}!")
    return sentiment_model, sentiment_tokenizer

# ----------------------------------------------------------------------
# Text Cleaning (used for BOTH prediction & SHAP)
# ----------------------------------------------------------------------

def text_cleaning(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    nlp = get_nlp()
    # 1. Replace entities
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in {"PERSON", "ORG", "GPE", "MONEY", "DATE"}:
            text = text.replace(ent.text, f"<{ent.label_}>")

    # 2. Lowercase + remove URLs, emails, numbers
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|[\w\.-]+@[\w\.-]+|\d+', ' ', text)

    # 3. Keep only letters, spaces, and <TAG>
    text = re.sub(r"[^a-z\s<>]", "", text)

    # 4. Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    EN_STOPWORDS = get_spacy_stopwords()
    #5. Remove stopwords (but keep <TAG>)
    words = [
        w for w in text.split()
        if w not in EN_STOPWORDS and w not in {"<person>", "<org>", "<gpe>", "<money>", "<date>"}
    ]
    return " ".join(words)

# ----------------------------------------------------------------------
# Prediction
# ----------------------------------------------------------------------

def predict_sentiment(text):
    if not text.strip():
        raise ValueError("Text is empty after cleaning")

    inputs = sentiment_tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512,
    )
    inputs = {k: v.to(sentiment_model.device) for k, v in inputs.items()}

    with torch.no_grad():
        logits = sentiment_model(**inputs).logits
        probs = torch.nn.functional.softmax(logits, dim=-1)
        pred_idx = torch.argmax(probs, dim=-1).item()
        confidence = probs[0][pred_idx].item()

    probabilities = {id2label[i]: float(probs[0][i]) for i in range(probs.shape[1])}
    return id2label[pred_idx], confidence, probabilities, pred_idx

# ----------------------------------------------------------------------
# SHAP Explanation with FULL WORD RECONSTRUCTION
# ----------------------------------------------------------------------

def generate_shap_explanation(text, pred_idx, top_k=3):
    try:
        device = sentiment_model.device

        # Use original text with <DATE>, <GPE> for model
        model_text = text

        # Clean version for display (optional: remove <tags>)
        display_text = re.sub(r"<[^>]+>", "", text).strip()

        # ----- FIXED: predict_proba handles SHAP's nested lists -----
        def predict_proba(texts):
            if isinstance(texts, str):
                texts = [texts]
            elif isinstance(texts, (list, np.ndarray)):
                flattened = []
                for item in texts:
                    if isinstance(item, (list, np.ndarray)):
                        flattened.extend([str(t) for t in item])
                    else:
                        flattened.append(str(item))
                texts = flattened
            else:
                texts = [str(texts)]
            texts = [t for t in texts if t.strip()]
            if not texts:
                raise ValueError("No valid text")
            enc = sentiment_tokenizer(texts, return_tensors="pt", truncation=True, padding=True, max_length=512)
            enc = {k: v.to(device) for k, v in enc.items()}
            with torch.no_grad():
                probs = torch.nn.functional.softmax(sentiment_model(**enc).logits, dim=-1)
            return probs.cpu().numpy()

        masker = shap.maskers.Text(sentiment_tokenizer)
        explainer = shap.Explainer(predict_proba, masker)
        shap_vals = explainer([model_text])  # ← Now works!

        # ----- Reconstruct words from display_text (no <tags>) -----
        encoded = sentiment_tokenizer(
            display_text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            return_offsets_mapping=True
        )
        offsets = encoded["offset_mapping"][0]
        raw_values = shap_vals[0].values[:, pred_idx]

        word_to_value = {}
        current_word = ""
        current_value = 0.0

        for i, (start, end) in enumerate(offsets.tolist()):
            if start == end == 0: continue
            span = display_text[start:end]
            value = raw_values[i]
            if start == 0 or display_text[start-1] == " ":
                if current_word: word_to_value[current_word] = current_value
                current_word = span
                current_value = value
            else:
                current_word += span
                current_value += value
        if current_word: word_to_value[current_word] = current_value

        sorted_items = sorted(word_to_value.items(), key=lambda x: abs(x[1]), reverse=True)
        tokens = np.array([w for w, v in sorted_items])
        values = np.array([v for w, v in sorted_items])

        # ----- Plot -----
        plt.figure(figsize=(10, 6))
        expl = shap.Explanation(values=values, base_values=shap_vals.base_values[0][pred_idx], data=tokens, feature_names=tokens)
        shap.waterfall_plot(expl, max_display=15, show=False)

        buf = BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=100)
        plt.close()
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode()

        # ----- Text explanation -----
        top = sorted_items[:top_k]
        parts = [f"'{w}' {'supports' if v > 0 else 'opposes'} {id2label[pred_idx]}" for w, v in top]
        textual = f"The sentiment is {id2label[pred_idx]} because " + ", ".join(parts) + "."

        return img_b64, textual

    except Exception as e:
        import traceback, sys
        traceback.print_exc(file=sys.stderr)
        return None, "SHAP failed."
# ----------------------------------------------------------------------
# Helper – get the text that will be analysed
# ----------------------------------------------------------------------

def get_text_for_analysis(payload: dict) -> str:
    """
    Returns the text that should be fed to the sentiment model:
      • If payload contains "id" → fetch article summary (summarize_article_by_id)
      • Else → use payload["text"] (raw article body)
    """
    article_id = payload.get("id")
    if article_id:
        # `summarize_article_by_id` is the function you already have
        summary = summarize_article_by_id(article_id)
        if not summary:
            raise ValueError("Could not generate a summary for the given article ID")
        return summary.strip()

    raw_text = payload.get("text", "")
    if not raw_text:
        raise ValueError("Neither 'id' nor 'text' was provided")
    return raw_text.strip()
# ----------------------------------------------------------------------
# Django View
# ----------------------------------------------------------------------

@csrf_exempt
def analyze_sentiment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    # ------------------------------------------------------------------
    # 1. Parse JSON payload
    # ------------------------------------------------------------------
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # ------------------------------------------------------------------
    # 2. Get the text that will be analysed (summary OR raw text)
    # ------------------------------------------------------------------
    try:
        text_to_analyse = get_text_for_analysis(payload)
    except ValueError as ve:
        return JsonResponse({"error": str(ve)}, status=400)

    # ------------------------------------------------------------------
    # 3. Clean the text (same cleaning you already use)
    # ------------------------------------------------------------------
    clean_text = text_cleaning(text_to_analyse)
    print("Cleaned text:", clean_text)

    if not clean_text.strip():
        return JsonResponse({"error": "No usable text after cleaning"}, status=400)

    # ------------------------------------------------------------------
    # 4. Load model (lazy)
    # ------------------------------------------------------------------
    if sentiment_model is None:
        load_sentiment_model()

    # ------------------------------------------------------------------
    # 5. Run sentiment + SHAP
    # ------------------------------------------------------------------
    try:
        sentiment, conf, probs, pred_idx = predict_sentiment(clean_text)
        shap_img, txt_expl = generate_shap_explanation(clean_text, pred_idx)

        return JsonResponse({
            "success": True,
            "sentiment": sentiment,
            "confidence": round(conf, 4),
            "probabilities": {k: round(v, 4) for k, v in probs.items()},
            "waterfall_plot": shap_img,
            "textual_explanation": txt_expl,
            # optional – let the frontend know what was actually analysed
            "analysed_text": clean_text,
        })

    except ValueError as ve:
        return JsonResponse({"error": f"Validation: {ve}"}, status=400)
    except Exception as e:
        import traceback, sys
        traceback.print_exc(file=sys.stderr)
        return JsonResponse({"error": f"Server error: {e}"}, status=500)