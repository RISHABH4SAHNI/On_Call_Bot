from typing import Optional
from services.embedding_service import (
    EmbeddingService, 
    OpenAIEmbeddingService, 
    OllamaEmbeddingService, 
    PerplexityEmbeddingService
)

class EmbeddingFactory:
    @staticmethod
    def create_service(service_type: str, **kwargs) -> EmbeddingService:
        service_type = service_type.lower()
        
        if service_type == "openai":
            return OpenAIEmbeddingService(**kwargs)
        elif service_type == "ollama":
            return OllamaEmbeddingService(**kwargs)
        elif service_type == "perplexity":
            return PerplexityEmbeddingService(**kwargs)
        else:
            raise ValueError(f"Unknown embedding service type: {service_type}")
    
    @staticmethod
    def get_available_services():
        return ["openai", "ollama", "perplexity"]
