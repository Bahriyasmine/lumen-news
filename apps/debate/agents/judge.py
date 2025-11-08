# apps/debate/agents/judge.py
from crewai import Agent, LLM
from decouple import config
import os

os.environ["GROQ_API_KEY"] = config('GROQ_API_KEY')

def create_judge_agent(agents_config, callback=None) -> Agent:
    llm_config = {
        "model": "groq/llama-3.3-70b-versatile",  # Add groq/ prefix
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    llm = LLM(**llm_config)
    
    return Agent(
        config=agents_config['judge_agent'],
        llm=llm,
        max_iter=1,
        verbose=True
    )