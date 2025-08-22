from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import openai
import requests
import os

class QueryEnhancementService(ABC):
    @abstractmethod
    def enhance_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        pass

class OpenAIQueryEnhancer(QueryEnhancementService):
    def __init__(self, api_key: Optional[str] = None):
        self.client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))

    def enhance_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        prompt = self._build_enhancement_prompt(query, context)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Enhance technical queries with relevant context while preserving original intent."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return query

    def _build_enhancement_prompt(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        context_info = ""
        if context:
            if context.get('repo_name'):
                context_info += f"Repository: {context['repo_name']}\n"
            if context.get('tech_stack'):
                context_info += f"Tech Stack: {', '.join(context['tech_stack'])}\n"
        
        return f"""
{context_info}
Original Query: {query}

Enhance this query with technical context for better code search. Preserve all original terms and add relevant technical concepts.
Enhanced Query:"""

class PerplexityQueryEnhancer(QueryEnhancementService):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai"

    def enhance_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        prompt = self._build_enhancement_prompt(query, context)
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                    "temperature": 0.1
                },
                timeout=15
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
        except Exception:
            pass
        return query

    def _build_enhancement_prompt(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        return f"Enhance this technical query with context: {query}"

class OllamaQueryEnhancer(QueryEnhancementService):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    def enhance_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": "codellama:7b",
                    "prompt": f"Enhance this technical query: {query}",
                    "stream": False,
                    "options": {"temperature": 0.1, "max_tokens": 200}
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('response', query).strip()
        except Exception:
            pass
        return query
