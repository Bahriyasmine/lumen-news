# chatbot/urls.py
from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Main chat interface
    path('', views.chat_page, name='chat_page'),
    
    # Existing endpoint (enhanced with web search)
    path('api/chat/', views.chat_api, name='chat_api'),
    
    # NEW: Voice chat endpoint
    path('api/chat-voice/', views.chat_voice_api, name='chat_voice_api'),
    
    # NEW: Text-to-Speech endpoint
    path('api/tts/', views.tts_api, name='tts_api'),
    
    # NEW: Serve audio files
    path('api/audio/<str:filename>', views.serve_audio, name='serve_audio'),
    
    # Stats endpoint
    path('api/stats/', views.stats_api, name='stats_api'),
    
]