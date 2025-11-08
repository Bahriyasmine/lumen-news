# apps/debate/tools/search_tool.py
from crewai.tools import tool
import requests
from decouple import config
import os

os.environ["SERPER_API_KEY"] = config('SERPER_API_KEY')

@tool("web_search")
def web_search_tool(query: str) -> str:
    """
    Search the web for current information to verify claims and find evidence.
    
    Args:
        query: Search query string (e.g., "fact check climate change statistics 2024")
    
    Returns:
        Formatted search results with titles, snippets, and links
    """
    try:
        url = "https://google.serper.dev/search"
        
        payload = {
            "q": query,
            "num": 5
        }
        
        headers = {
            "X-API-KEY": os.environ["SERPER_API_KEY"],
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        results = response.json()
        
        formatted_results = []
        
        if "organic" in results:
            for i, result in enumerate(results["organic"][:5], 1):
                formatted_results.append(
                    f"{i}. {result.get('title', 'No title')}\n"
                    f"   {result.get('snippet', 'No snippet')}\n"
                    f"   Source: {result.get('link', 'No link')}\n"
                )
        
        if not formatted_results:
            return "No relevant search results found."
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Search error: {str(e)}"