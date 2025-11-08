from django.shortcuts import render
from django.http import StreamingHttpResponse
from apps.debate.crew import DebateCrew
from apps.debate.streaming import StreamingCallback
from django.shortcuts import render, get_object_or_404
from apps.scraper.models import Article
import json
import threading


# Create ONE shared streaming wrapper in views.py
import litellm
def debate_page(request, article_id=None):
    """Render the debate interface – with or without an article"""
    context = {}

    if article_id:
        article = get_object_or_404(Article, id=article_id)
        context.update({
            'article_id': article.id,
            'article_title': article.title,
            'article_text': article.text,
            'article_source': article.source,
        })

    return render(request, 'debate.html', context)

def stream_debate(request):
    article = request.GET.get('article', """...""")
    context = request.GET.get('context', 'No additional context')
    
    def event_stream():
        callback = StreamingCallback()
        
        # Store original ONCE
        if not hasattr(litellm, '_debate_original_completion'):
            litellm._debate_original_completion = litellm.completion
        
        agent_execution_counts = {'defender': 0, 'opposer': 0, 'judge': 0}
        current_task_index = [0]  # Mutable to track in closure
        
        def smart_streaming_wrapper(*args, **kwargs):
            """Single wrapper that determines agent from task order"""
            
            # Task execution order: defender1, opposer1, defender2, opposer2, judge
            task_order = [
                ('defender', 1),
                ('opposer', 1),
                ('defender', 2),
                ('opposer', 2),
                ('judge', None)
            ]
            
            if current_task_index[0] < len(task_order):
                agent, round_num = task_order[current_task_index[0]]
                current_task_index[0] += 1
                
                callback.set_context(agent, round_num)
            
            kwargs['stream'] = True
            response = litellm._debate_original_completion(*args, **kwargs)
            
            if hasattr(response, '__iter__'):
                full_content = []
                try:
                    for chunk in response:
                        callback(chunk)
                        if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                            delta = chunk.choices[0].delta
                            if hasattr(delta, 'content') and delta.content:
                                full_content.append(delta.content)
                except Exception as e:
                    print(f"❌ Error: {e}")
                
                class FakeResponse:
                    def __init__(self, content):
                        self.content = content
                        self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': content})()})()]
                
                return FakeResponse(''.join(full_content))
            return response
        
        # Patch litellm for this debate
        litellm.completion = smart_streaming_wrapper
        
        def run_debate():
            try:
                debate_crew = DebateCrew(streaming_callback=callback)
                debate_crew.crew().kickoff(inputs={
                    'article_text': article[:1200],
                    'full_article': article,
                    'num_rounds': 2,
                    'context': context
                })
                callback.queue.put({'type': 'complete'})
            except Exception as e:
                callback.queue.put({'type': 'error', 'message': str(e)})
            finally:
                # Restore original
                litellm.completion = litellm._debate_original_completion
        
        thread = threading.Thread(target=run_debate, daemon=True)
        thread.start()
        
        yield f"data: {json.dumps({'type': 'connected'})}\n\n"
        
        try:
            while True:
                event = callback.queue.get(timeout=120)
                yield f"data: {json.dumps(event)}\n\n"
                
                if event['type'] in ['complete', 'error']:
                    break
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response