# apps/users/views.py
# apps/users/views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
import json
from django.shortcuts import render, redirect
from django.views import View
from .forms import PreferenceForm


@login_required
@require_POST
@csrf_protect
def save_preferences(request):
    try:
        data = json.loads(request.body)
        prefs = request.user.profile.preferences
        
        # Save domains as list
        domains_str = data.get('domains', '')
        prefs.domains = [d.strip() for d in domains_str.split(',') if d.strip()]
        
        prefs.mental_state = data.get('mental_state', '')
        prefs.min_sentiment = data.get('min_sentiment')
        prefs.preferences_text = data.get('preferences_text', '')
        
        # Generate embedding (use your real BERT later)
        from . import embeddings
        text = " ".join(prefs.domains) + " " + prefs.preferences_text
        if text.strip():
            print("__________________ayoub__________________________",text)

            prefs.embedding = embeddings.create_user_embedding(text)
        prefs.save()
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class OnboardingView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('signin')
        
        # Always show form — pre-filled if preferences exist
        prefs = request.user.profile.preferences
        form = PreferenceForm(instance=prefs)  # ← Pre-fill with existing data
        return render(request, 'onboarding.html', {'form': form})
    
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('signin')
        
        prefs = request.user.profile.preferences
        form = PreferenceForm(request.POST, instance=prefs)  # ← Bind to existing instance
        
        if form.is_valid():
            prefs = form.save(commit=False)

            # Regenerate embedding
            from . import embeddings
            text = " ".join(prefs.domains) + " " + (prefs.preferences_text or "")
            if text.strip():
                print("__________________ayoub__________________________",text)
                prefs.embedding = embeddings.create_user_embedding(text)
            prefs.save()
            
            return redirect('home')
        
        # If form invalid, re-render with errors
        return render(request, 'onboarding.html', {'form': form})

