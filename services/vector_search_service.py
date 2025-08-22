from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch
from models.function_model import FunctionMetadata, SearchResult
from services.embedding_service import EmbeddingService

class VectorSearchService:
    def __init__(self, embedding_service: EmbeddingService):
        self.client = OpenSearch([{"host": "localhost", "port": 9200}], 
                                http_auth=("admin", "admin"), 
                                use_ssl=False)
        self.embedding_service = embedding_service
        self.index_name = "code_embeddings"

    def setup_index(self):
        if not self.client.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "embedding": {"type": "dense_vector", "dims": 3072},
                        "embedding_knn": {"type": "knn_vector", "dimension": 3072},
                        "func_name": {"type": "keyword"},
                        "lookup_id": {"type": "keyword"},
                        "file_path": {"type": "keyword"},
                        "repository_name": {"type": "keyword"},
                        "module_name": {"type": "keyword"},
                        "code": {"type": "text"},
                        "calls": {"type": "keyword"},
                        "is_async": {"type": "boolean"},
                        "start_line": {"type": "integer"},
                        "end_line": {"type": "integer"},
                        "class_context": {"type": "keyword"},
                        "nested_call_ids": {"type": "keyword"},
                        "decorators": {"type": "keyword"},
                        "error_handling": {"type": "object"}
                    }
                }
            }
            self.client.indices.create(index=self.index_name, body=mapping)

    def store_function(self, function: FunctionMetadata, embedding: List[float]) -> bool:
        doc = {
            "embedding": embedding,
            "embedding_knn": embedding,
            "func_name": function.name,
            "lookup_id": function.lookup_id,
            "file_path": function.file_path,
            "repository_name": function.repository_name,
            "module_name": function.module_name,
            "code": function.code,
            "calls": function.calls,
            "is_async": function.is_async,
            "start_line": function.start_line,
            "end_line": function.end_line,
            "class_context": function.class_context,
            "nested_call_ids": function.nested_call_ids,
            "decorators": function.decorators,
            "error_handling": function.error_handling
        }
        
        try:
            self.client.index(index=self.index_name, id=function.lookup_id, body=doc)
            return True
        except Exception:
            return False

    def search_functions(self, query: str, limit: int = 5) -> List[SearchResult]:
        query_embedding = self.embedding_service.create_query_embedding(query)
        if not query_embedding:
            return []

        search_body = {
            "query": {
                "knn": {
                    "embedding_knn": {
                        "vector": query_embedding,
                        "k": limit * 2
                    }
                }
            },
            "size": limit
        }

        try:
            response = self.client.search(index=self.index_name, body=search_body)
            hits = response.get('hits', {}).get('hits', [])
            
            results = []
            for hit in hits:
                source = hit['_source']
                function_metadata = self._build_function_metadata(source)
                
                search_result = SearchResult(
                    function_metadata=function_metadata,
                    relevance_score=hit['_score'],
                    search_method="vector_similarity",
                    match_type="semantic"
                )
                results.append(search_result)
            
            return results
        except Exception:
            return []

    def get_function_by_id(self, lookup_id: str) -> Optional[FunctionMetadata]:
        try:
            response = self.client.get(index=self.index_name, id=lookup_id)
            source = response['_source']
            return self._build_function_metadata(source)
        except Exception:
            return None

    def _build_function_metadata(self, source: Dict[str, Any]) -> FunctionMetadata:
        return FunctionMetadata(
            name=source['func_name'],
            lookup_id=source['lookup_id'],
            file_path=source['file_path'],
            repository_name=source['repository_name'],
            module_name=source['module_name'],
            nested_call_ids=source.get('nested_call_ids', []),
            start_line=source['start_line'],
            end_line=source['end_line'],
            code=source['code'],
            is_async=source['is_async'],
            class_context=source.get('class_context'),
            calls=source['calls'],
            imports=[],
            decorators=source.get('decorators', []),
            error_handling=source.get('error_handling', {}),
            line_numbers=list(range(source['start_line'], source['end_line'] + 1))
        )
