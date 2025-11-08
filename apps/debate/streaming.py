# streaming.py - Add agent tracking
from typing import Any, Dict
import queue
import threading

class StreamingCallback:
    """Captures LLM tokens in real-time"""
    
    def __init__(self):
        self.queue = queue.Queue()
        self.current_agent = None
        self.current_round = None
        self.call_count = 0
        self.agent_call_counts = {'defender': 0, 'opposer': 0, 'judge': 0}
        self.lock = threading.Lock()
    
    def set_context(self, agent: str, round_num: int):
        """Set which agent is speaking"""
        with self.lock:
            self.current_agent = agent
            self.current_round = round_num
            self.queue.put({
                'type': 'agent_start',
                'agent': agent,
                'round': round_num
            })
            print(f"🎯 Context set: {agent} - Round {round_num}")
    
    def __call__(self, chunk):
        """Called by LLM for each token"""
        self.call_count += 1
        
        try:
            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                
                if hasattr(delta, 'content') and delta.content:
                    with self.lock:
                        self.queue.put({
                            'type': 'token',
                            'agent': self.current_agent,
                            'round': self.current_round,
                            'token': delta.content
                        })
                    return
            
            elif isinstance(chunk, dict):
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    content = chunk['choices'][0].get('delta', {}).get('content')
                    if content:
                        with self.lock:
                            self.queue.put({
                                'type': 'token',
                                'agent': self.current_agent,
                                'round': self.current_round,
                                'token': content
                            })
                        return
            
            elif isinstance(chunk, str) and chunk.strip():
                with self.lock:
                    self.queue.put({
                        'type': 'token',
                        'agent': self.current_agent,
                        'round': self.current_round,
                        'token': chunk
                    })
                return
                
        except Exception as e:
            print(f"❌ Streaming callback error: {e}")