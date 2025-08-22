from factories.embedding_factory import EmbeddingFactory
from factories.llm_factory import LLMFactory
from services.vector_search_service import VectorSearchService
from core.repository_processor import RepositoryProcessor
from core.function_lookup import FunctionLookupTable

class ServiceFactory:
    def __init__(self):
        self._embedding_service = None
        self._search_service = None
        self._analysis_service = None
        self._query_enhancer = None
        self._repo_processor = None
        self._lookup_table = None
    
    def get_embedding_service(self, service_type: str = "openai"):
        if not self._embedding_service:
            self._embedding_service = EmbeddingFactory.create_service(service_type)
        return self._embedding_service
    
    def get_search_service(self, embedding_service_type: str = "openai"):
        if not self._search_service:
            embedding_service = self.get_embedding_service(embedding_service_type)
            self._search_service = VectorSearchService(embedding_service)
        return self._search_service
    
    def get_analysis_service(self, service_type: str = "openai"):
        if not self._analysis_service:
            self._analysis_service = LLMFactory.create_analysis_service(service_type)
        return self._analysis_service
    
    def get_query_enhancer(self, service_type: str = "openai"):
        if not self._query_enhancer:
            self._query_enhancer = LLMFactory.create_query_enhancer(service_type)
        return self._query_enhancer
    
    def get_repository_processor(self):
        if not self._repo_processor:
            self._repo_processor = RepositoryProcessor()
        return self._repo_processor
    
    def get_lookup_table(self):
        if not self._lookup_table:
            self._lookup_table = FunctionLookupTable()
        return self._lookup_table
