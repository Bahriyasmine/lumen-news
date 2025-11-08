# opposer.py
from crewai import Agent, LLM
from decouple import config
import os

os.environ["GROQ_API_KEY"] = config('GROQ_API_KEY')

_opposer_execution_count = 0

def create_opposer_agent(agents_config, callback=None) -> Agent:
     llm_config = {
        "model": "groq/llama-3.1-8b-instant",
        "temperature": 0.7,
        "max_tokens": 500
    }
    
     llm = LLM(**llm_config)
    
     return Agent(
        config=agents_config['opposer_agent'],
        llm=llm,
        max_iter=1,
        verbose=True
    )