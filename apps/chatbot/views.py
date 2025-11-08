from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
from pathlib import Path
from .chatbot_rag import get_chatbot
from .models import ChatHistory


def chat_page(request):
    """Render chat interface"""
    return render(request, 'chatbot/chat.html')


@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """
    Chat endpoint (LOCAL RAG ONLY)
    """
    try:
        data = json.loads(request.body)
        user_message = (data.get('message') or data.get('question') or '').strip()
        session_id = data.get('session_id', 'default')

        if not user_message:
            return JsonResponse({'success': False, 'error': 'Message is required'}, status=400)

        chatbot = get_chatbot()
        result = chatbot.chat(user_message)

        if result.get('success'):
            try:
                ChatHistory.objects.create(
                    session_id=session_id,
                    user_message=user_message,
                    bot_response=result.get('response', '')
                )
            except Exception:
                pass

        return JsonResponse({
            'success': bool(result.get('success')),
            'response': result.get('response', ''),
            'sources': result.get('sources', []),
            'error': result.get('error') if not result.get('success') else None
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def chat_voice_api(request):
    """
    Voice chat endpoint (STT → Chat → optional TTS)
    Returns: transcript + response (+ audio_url)
    """
    try:
        if 'audio' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'Audio file is required'}, status=400)

        audio_file = request.FILES['audio']

        # Save uploaded audio temporarily
        temp_audio_path = default_storage.save(
            f'temp_audio/{audio_file.name}',
            ContentFile(audio_file.read())
        )
        full_temp_path = default_storage.path(temp_audio_path)

        chatbot = get_chatbot()

        # 1) STT
        stt_result = chatbot.speech_to_text(full_temp_path)
        if not stt_result.get('success'):
            default_storage.delete(temp_audio_path)
            return JsonResponse({'success': False, 'error': f"Speech recognition failed: {stt_result.get('error')}"}, status=500)

        transcript = (stt_result.get('text') or '').strip()
        if not transcript:
            default_storage.delete(temp_audio_path)
            return JsonResponse({'success': False, 'error': 'Empty transcription'}, status=500)

        # 2) Local chat
        chat_result = chatbot.chat(transcript)
        if not chat_result.get('success'):
            default_storage.delete(temp_audio_path)
            return JsonResponse(chat_result, status=500)

        # 3) TTS (optional)
        tts_result = chatbot.text_to_speech(chat_result.get('response', ''))

        # Cleanup temp audio
        default_storage.delete(temp_audio_path)

        # Save history (non-blocking)
        try:
            ChatHistory.objects.create(
                session_id='voice_' + str(hash(transcript))[:10],
                user_message=transcript,
                bot_response=chat_result.get('response', '')
            )
        except Exception:
            pass

        audio_url = None
        if tts_result.get('success'):
            audio_path = Path(tts_result['audio_path'])
            audio_url = f"/chatbot/api/audio/{audio_path.name}"

        return JsonResponse({
            'success': True,
            'transcript': transcript,   # UI shows this as the user's bubble
            'question': transcript,     # backward-compat key
            'response': chat_result.get('response', ''),
            'sources': chat_result.get('sources', []),
            'audio_url': audio_url,
            'language': stt_result.get('language', 'en')
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def tts_api(request):
    """Text-to-Speech → returns audio_url"""
    try:
        data = json.loads(request.body)
        text = (data.get('text') or '').strip()
        language = data.get('language', 'en')
        slow = bool(data.get('slow', False))

        if not text:
            return JsonResponse({'success': False, 'error': 'Text is required'}, status=400)

        chatbot = get_chatbot()
        result = chatbot.text_to_speech(text, language=language, slow=slow)

        if result.get('success'):
            audio_path = Path(result['audio_path'])
            audio_url = f"/chatbot/api/audio/{audio_path.name}"
            return JsonResponse({'success': True, 'audio_url': audio_url, 'cached': result.get('cached', False)})
        else:
            return JsonResponse(result, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def serve_audio(request, filename):
    """Serve generated TTS audio"""
    try:
        chatbot = get_chatbot()
        audio_path = chatbot.audio_dir / filename
        if not audio_path.exists():
            return JsonResponse({'error': 'Audio file not found'}, status=404)
        return FileResponse(open(audio_path, 'rb'), content_type='audio/mpeg', as_attachment=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def stats_api(request):
    """Stats"""
    try:
        chatbot = get_chatbot()
        return JsonResponse(chatbot.get_stats())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



