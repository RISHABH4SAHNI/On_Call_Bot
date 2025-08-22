from abc import ABC, abstractmethod
from typing import List, Optional
import openai
import requests
import os
from models.function_model import FunctionMetadata

class EmbeddingService(ABC):
    @abstractmethod
    def create_embedding(self, function: FunctionMetadata) -> Optional[List[float]]:
        pass

    @abstractmethod
    def create_query_embedding(self, query: str) -> Optional[List[float]]:
        pass

class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self, api_key: Optional[str] = None):
        self.client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.model = "text-embedding-3-large"

    def create_embedding(self, function: FunctionMetadata) -> Optional[List[float]]:
        context = self._build_context(function)
        return self._embed_text(context)

    def create_query_embedding(self, query: str) -> Optional[List[float]]:
        return self._embed_text(query)

    def _build_context(self, function: FunctionMetadata) -> str:
        context_parts = [
            f"Function: {function.name}",
            f"Repository: {function.repository_name}",
            f"Module: {function.module_name}",
            f"Type: {'async' if function.is_async else 'sync'}",
        ]
        
        if function.class_context:
            context_parts.append(f"Class: {function.class_context}")
        
        if function.decorators:
            context_parts.append(f"Decorators: {', '.join(function.decorators)}")
        
        if function.calls:
            context_parts.append(f"Calls: {', '.join(function.calls[:10])}")
        
        if function.error_handling.get('has_try_catch'):
            context_parts.append("Error handling: Has try-catch blocks")
            if function.error_handling.get('error_types'):
                context_parts.append(f"Handles: {', '.join(function.error_handling['error_types'])}")
        
        context_parts.append(f"Code:\n{function.code}")
        
        return '\n'.join(context_parts)

    def _embed_text(self, text: str) -> Optional[List[float]]:
        try:
            response = self.client.embeddings.create(model=self.model, input=text)
            return response.data[0].embedding
        except Exception:
            return None

class OllamaEmbeddingService(EmbeddingService):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.base_url = base_url
        self.model = model

    def create_embedding(self, function: FunctionMetadata) -> Optional[List[float]]:
        context = self._build_context(function)
        return self._embed_text(context)

    def create_query_embedding(self, query: str) -> Optional[List[float]]:
        return self._embed_text(query)

    def _build_context(self, function: FunctionMetadata) -> str:
        context_parts = [
            f"Function: {function.name}",
            f"Repository: {function.repository_name}",
            f"Module: {function.module_name}",
            f"Code:\n{function.code}"
        ]
        return '\n'.join(context_parts)

    def _embed_text(self, text: str) -> Optional[List[float]]:
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()["embedding"]
        except Exception:
            pass
        return None

class PerplexityEmbeddingService(EmbeddingService):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai"
        self.model = "text-embedding-3-large"

    def create_embedding(self, function: FunctionMetadata) -> Optional[List[float]]:
        context = self._build_context(function)
        return self._embed_text(context)

    def create_query_embedding(self, query: str) -> Optional[List[float]]:
        return self._embed_text(query)

    def _build_context(self, function: FunctionMetadata) -> str:
        return f"Function: {function.name}\nCode:\n{function.code}"

    def _embed_text(self, text: str) -> Optional[List[float]]:
        try:
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={"model": self.model, "input": text},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()['data'][0]['embedding']
        except Exception:
            pass
        return None
