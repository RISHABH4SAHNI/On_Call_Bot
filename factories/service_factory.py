from services.embedding_service import OpenAIEmbeddingService, OllamaEmbeddingService, PerplexityEmbeddingService
from services.vector_search_service import VectorSearchService
from services.call_graph_search_service import CallGraphSearchService
from services.query_enhancement_service import OpenAIQueryEnhancementService, PerplexityQueryEnhancementService, OllamaQueryEnhancementService
from services.analysis_service import OpenAIAnalysisService, PerplexityAnalysisService, OllamaAnalysisService
from core.call_graph_processor import CallGraphProcessor
from core.function_lookup import FunctionLookupTable
from core.repository_processor import RepositoryProcessor
from models.function_model import AnalysisApproach

class ServiceFactory:
    def __init__(self):
        pass

    def get_embedding_service(self, service_type: str = "openai"):
        if service_type == "openai":
            return OpenAIEmbeddingService()
        elif service_type == "ollama":
            return OllamaEmbeddingService()
        elif service_type == "perplexity":
            return PerplexityEmbeddingService()
        else:
            raise ValueError(f"Unsupported embedding service: {service_type}")

    def get_search_service(self, embedding_service_type: str = "openai"):
        embedding_service = self.get_embedding_service(embedding_service_type)
        return VectorSearchService(embedding_service)
    
    def get_call_graph_search_service(self, embedding_service_type: str = "openai"):
        embedding_service = self.get_embedding_service(embedding_service_type)
        return CallGraphSearchService(embedding_service)
    
    def get_call_graph_processor(self):
        return CallGraphProcessor()
    
    def get_combined_search_service(self, embedding_service_type: str = "openai", approach: str = "function_lookup_table"):
        if approach == "call_graph":
            return self.get_call_graph_search_service(embedding_service_type)
        else:
            return self.get_search_service(embedding_service_type)
    
    def get_query_enhancer(self, service_type: str = "openai"):
        if service_type == "openai":
            return OpenAIQueryEnhancementService()
        elif service_type == "perplexity":
            return PerplexityQueryEnhancementService()
        elif service_type == "ollama":
            return OllamaQueryEnhancementService()
        else:
            raise ValueError(f"Unsupported query enhancement service: {service_type}")

    def get_analysis_service(self, service_type: str = "openai"):
        if service_type == "openai":
            return OpenAIAnalysisService()
        elif service_type == "perplexity":
            return PerplexityAnalysisService()
        elif service_type == "ollama":
            return OllamaAnalysisService()
        else:
            raise ValueError(f"Unsupported analysis service: {service_type}")

    def get_repository_processor(self):
        return RepositoryProcessor()

    def get_lookup_table(self):
        return FunctionLookupTable()
    
    def get_services_for_approach(self, approach: str, embedding_service_type: str = "openai", llm_service_type: str = "openai"):
        """Get all required services for a specific analysis approach"""
        services = {
            'embedding_service': self.get_embedding_service(embedding_service_type),
            'query_enhancer': self.get_query_enhancer(llm_service_type),
            'analysis_service': self.get_analysis_service(llm_service_type),
            'repository_processor': self.get_repository_processor(),
        }
        
        if approach == "call_graph":
            services.update({
                'search_service': self.get_call_graph_search_service(embedding_service_type),
                'call_graph_processor': self.get_call_graph_processor()
            })
        else:
            services.update({
                'search_service': self.get_search_service(embedding_service_type),
                'lookup_table': self.get_lookup_table()
            })
        
        return services
    
    def validate_approach(self, approach: str) -> bool:
        """Validate if the analysis approach is supported"""
        from config.settings import SUPPORTED_APPROACHES
        return approach in SUPPORTED_APPROACHES
    
    def get_supported_approaches(self):
        """Get list of supported analysis approaches"""
        return [
            {
                'key': 'function_lookup_table',
                'name': 'Function Lookup Table',
                'description': 'Traditional approach using function metadata and nested calls'
            },
            {
                'key': 'call_graph',
                'name': 'Call Graph',
                'description': 'Advanced approach using function call graph for dependency analysis'
            }
        ]
