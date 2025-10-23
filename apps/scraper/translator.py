from transformers import MarianMTModel, MarianTokenizer

# Function to chunk text to fit token limits
def chunk_text_chars(text, tokenizer, max_chars=1000, max_tokens=512):
    chunks = []
    for i in range(0, len(text), max_chars):
        chunk = text[i:i + max_chars]
        tokens = tokenizer(chunk, add_special_tokens=False, return_tensors="pt")["input_ids"][0]
        if len(tokens) <= max_tokens:
            chunks.append(chunk)
        else:
            trimmed_chunk = chunk[:max_chars]
            last_space = trimmed_chunk.rfind(' ')
            if last_space > 0:
                trimmed_chunk = trimmed_chunk[:last_space]
            chunks.append(trimmed_chunk)
    return chunks

# French translation
def translate_to_french(text, device="cpu"):
    model_name = "Helsinki-NLP/opus-mt-en-fr"
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name).to(device)
    
    chunks = chunk_text_chars(text, tokenizer)
    translations = []
    for chunk in chunks:
        inputs = tokenizer(chunk, max_length=512, truncation=True, return_tensors="pt", padding=True).to(device)
        translated_ids = model.generate(**inputs, max_length=512, num_beams=4, early_stopping=True)
        translation = tokenizer.decode(translated_ids[0], skip_special_tokens=True)
        translations.append(translation)
    return " ".join(translations)

# Arabic translation
def translate_to_arabic(text, device="cpu"):
    model_name = "Helsinki-NLP/opus-mt-en-ar"
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name).to(device)
    
    chunks = chunk_text_chars(text, tokenizer)
    translations = []
    for chunk in chunks:
        inputs = tokenizer(chunk, max_length=512, truncation=True, return_tensors="pt", padding=True).to(device)
        translated_ids = model.generate(**inputs, max_length=512, num_beams=4, early_stopping=True)
        translation = tokenizer.decode(translated_ids[0], skip_special_tokens=True)
        translations.append(translation)
    return " ".join(translations)
