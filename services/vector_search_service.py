import logging
import os
import time
from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch
from opensearchpy.connection import RequestsHttpConnection
from opensearchpy.exceptions import ConnectionError, RequestError, NotFoundError
from models.function_model import FunctionMetadata, SearchResult, AnalysisApproach
from services.embedding_service import EmbeddingService
from config.settings import get_opensearch_config, INDEX_CONFIG, MAX_FUNCTIONS_PER_SEARCH

class VectorSearchService:
    def __init__(self, embedding_service: EmbeddingService):
        self.logger = logging.getLogger(__name__)
        # Use configuration from settings with environment variable overrides
        config = get_opensearch_config()
        
        self.client = OpenSearch(
            config['hosts'],
            http_auth=config['http_auth'],
            use_ssl=config['use_ssl'],
            verify_certs=config.get('verify_certs', False),
            connection_class=RequestsHttpConnection,
            timeout=config.get('timeout', 30),
            max_retries=config.get('max_retries', 3),
            retry_on_timeout=config.get('retry_on_timeout', True)
        )
        self.embedding_service = embedding_service
        self.index_name = INDEX_CONFIG['name']
        self.embedding_dimensions = embedding_service.get_embedding_dimensions()
        
        # Validate connection on initialization
        self._validate_connection()
    
    def _validate_connection(self) -> bool:
        """Validate OpenSearch connection with retries"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Test connection with a simple cluster health check
                health = self.client.cluster.health(timeout='5s')
                if health.get('status') in ['green', 'yellow']:
                    self.logger.info(f"OpenSearch connection validated. Cluster status: {health.get('status')}")
                    return True
                else:
                    self.logger.warning(f"OpenSearch cluster status is {health.get('status')}")
            except ConnectionError as e:
                self.logger.warning(f"OpenSearch connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
            except Exception as e:
                self.logger.error(f"Unexpected error during OpenSearch connection validation: {e}")
                break
        
        self.logger.error("Failed to establish OpenSearch connection after all retries")
        raise ConnectionError("Cannot connect to OpenSearch cluster")
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the OpenSearch connection and index"""
        try:
            cluster_health = self.client.cluster.health()
            index_exists = self.client.indices.exists(index=self.index_name)
            return {
                'cluster_status': cluster_health.get('status'),
                'index_exists': index_exists,
                'embedding_dimensions': self.embedding_dimensions
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {'error': str(e)}

    def setup_index(self):
        """Setup the OpenSearch index with dynamic embedding dimensions"""
        try:
            if not self.client.indices.exists(index=self.index_name):
                # Update index configuration with correct embedding dimensions
                index_config = INDEX_CONFIG.copy()
                if 'mappings' in index_config and 'properties' in index_config['mappings']:
                    if 'embedding' in index_config['mappings']['properties']:
                        index_config['mappings']['properties']['embedding']['dims'] = self.embedding_dimensions
                    if 'embedding_knn' in index_config['mappings']['properties']:
                        index_config['mappings']['properties']['embedding_knn']['dimension'] = self.embedding_dimensions
                
                final_config = {
                    "settings": index_config['settings'],
                    "mappings": index_config['mappings']
                }
                self.client.indices.create(index=self.index_name, body=final_config)
                self.logger.info(f"Created index: {self.index_name} with {self.embedding_dimensions} dimensions")
            else:
                self.logger.debug(f"Index {self.index_name} already exists")
        except RequestError as e:
            self.logger.error(f"OpenSearch request error during index setup: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during index setup: {e}")
            raise

    def store_function(self, function: FunctionMetadata, embedding: List[float]) -> bool:
        """Store a function with its embedding in OpenSearch"""
        if not embedding or len(embedding) != self.embedding_dimensions:
            self.logger.warning(f"Invalid embedding dimensions for function {function.name}. Expected: {self.embedding_dimensions}, Got: {len(embedding) if embedding else 0}")
            return False
            
        # Validate function metadata
        if not function.lookup_id or not function.name:
            self.logger.warning(f"Invalid function metadata: {function}")
            return False
            
        doc = {
            "embedding": embedding,
            "embedding_knn": embedding,
            "func_name": function.name,
            "lookup_id": function.lookup_id,
            "file_path": function.file_path,
            "file_name": function.file_name or function.file_path.split('/')[-1],
            "repository_name": function.repository_name,
            "module_name": function.module_name,
            "code": function.code,
            "code_with_line_numbers": function.code_with_line_numbers,
            "calls": function.calls,
            "is_async": function.is_async,
            "start_line": function.start_line,
            "end_line": function.end_line,
            "class_context": function.class_context,
            "nested_call_ids": function.nested_call_ids,
            "decorators": function.decorators,
            "error_handling": function.error_handling,
            "imports": function.imports,
            "line_numbers": function.line_numbers
        }
        
        try:
            self.client.index(index=self.index_name, id=function.lookup_id, body=doc)
            self.logger.debug(f"Stored function: {function.name} ({function.lookup_id})")
            return True
        except RequestError as e:
            self.logger.error(f"OpenSearch request error storing function {function.name}: {e}")
            return False
        except ConnectionError as e:
            self.logger.error(f"OpenSearch connection error storing function {function.name}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to store function {function.name}: {e}")
            return False
    
    def store_functions_bulk(self, functions_with_embeddings: List[tuple]) -> Dict[str, Any]:
        """Store multiple functions efficiently using bulk operations"""
        if not functions_with_embeddings:
            return {'success': 0, 'failed': 0, 'errors': []}
        
        actions = []
        for function, embedding in functions_with_embeddings:
            if not embedding or len(embedding) != self.embedding_dimensions:
                continue
                
            if not function.lookup_id or not function.name:
                continue
            
            doc = {
                "embedding": embedding,
                "embedding_knn": embedding,
                "func_name": function.name,
                "lookup_id": function.lookup_id,
                "file_path": function.file_path,
                "file_name": function.file_name or function.file_path.split('/')[-1],
                "repository_name": function.repository_name,
                "module_name": function.module_name,
                "code": function.code,
                "code_with_line_numbers": function.code_with_line_numbers,
                "calls": function.calls,
                "is_async": function.is_async,
                "start_line": function.start_line,
                "end_line": function.end_line,
                "class_context": function.class_context,
                "nested_call_ids": function.nested_call_ids,
                "decorators": function.decorators,
                "error_handling": function.error_handling,
                "imports": function.imports,
                "line_numbers": function.line_numbers
            }
            
            actions.append({
                "_index": self.index_name,
                "_id": function.lookup_id,
                "_source": doc
            })
        
        if not actions:
            return {'success': 0, 'failed': 0, 'errors': ['No valid functions to store']}
        
        try:
            from opensearchpy.helpers import bulk
            success, failed = bulk(self.client, actions, index=self.index_name)
            self.logger.info(f"Bulk operation completed: {success} successful, {len(failed)} failed")
            return {
                'success': success,
                'failed': len(failed),
                'errors': [str(error) for error in failed] if failed else []
            }
        except Exception as e:
            self.logger.error(f"Bulk store operation failed: {e}")
            return {'success': 0, 'failed': len(actions), 'errors': [str(e)]}

    def search_functions(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Search for functions using vector similarity"""
        if not query or not query.strip():
            self.logger.warning("Empty query provided")
            return []
            
        # Validate and cap limit
        limit = min(max(1, limit), MAX_FUNCTIONS_PER_SEARCH)
        
        query_embedding = self.embedding_service.create_query_embedding(query)
        if not query_embedding:
            self.logger.warning("Failed to create query embedding")
            return []

        # Validate embedding dimensions
        if len(query_embedding) != self.embedding_dimensions:
            self.logger.error(f"Invalid query embedding dimensions: {len(query_embedding)}, expected: {self.embedding_dimensions}")
            return []

        search_body = {
            "query": {
                "knn": {
                    "embedding_knn": {
                        "vector": query_embedding,
                        "k": min(limit * 2, 100)  # Cap to prevent excessive results
                    }
                }
            },
            "size": limit,
            "_source": {
                "excludes": ["embedding", "embedding_knn"]  # Exclude large embedding fields
            }
        }

        try:
            response = self.client.search(index=self.index_name, body=search_body)
        except NotFoundError:
            self.logger.error(f"Index {self.index_name} not found")
            return []
        except RequestError as e:
            self.logger.error(f"OpenSearch request error during search: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
        
        try:
            hits = response.get('hits', {}).get('hits', [])
            
            if not hits:
                self.logger.info(f"No search results found for query: {query[:50]}...")
                return []
            
            results = []
            for hit in hits:
                source = hit['_source']
                function_metadata = self._build_function_metadata(source)
                
                if not function_metadata:
                    continue
                
                search_result = SearchResult(
                    function_metadata=function_metadata,
                    relevance_score=hit['_score'],
                    search_method="vector_similarity",
                    match_type="semantic",
                    approach_used=AnalysisApproach.FUNCTION_LOOKUP_TABLE
                )
                results.append(search_result)
            
            self.logger.info(f"Found {len(results)} search results for query")
            return results
        except Exception as e:
            self.logger.error(f"Error processing search results: {e}")
            return []

    def get_function_by_id(self, lookup_id: str) -> Optional[FunctionMetadata]:
        """Retrieve a specific function by its lookup ID"""
        if not lookup_id:
            return None
            
        try:
            response = self.client.get(
                index=self.index_name, 
                id=lookup_id,
                _source_excludes=["embedding", "embedding_knn"]
            )
            source = response['_source']
            return self._build_function_metadata(source)
        except NotFoundError:
            self.logger.debug(f"Function not found by ID {lookup_id}")
            return None
        except RequestError as e:
            self.logger.error(f"OpenSearch request error retrieving function {lookup_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving function by ID {lookup_id}: {e}")
            return None

    def _build_function_metadata(self, source: Dict[str, Any]) -> Optional[FunctionMetadata]:
        """Build FunctionMetadata object from OpenSearch source data"""
        try:
            return FunctionMetadata(
                name=source.get('func_name', ''),
                lookup_id=source.get('lookup_id', ''),
                file_path=source.get('file_path', ''),
                repository_name=source.get('repository_name', ''),
                module_name=source.get('module_name', ''),
                nested_call_ids=source.get('nested_call_ids', []),
                start_line=source.get('start_line', 0),
                end_line=source.get('end_line', 0),
                code=source.get('code', ''),
                is_async=source.get('is_async', False),
                class_context=source.get('class_context'),
                calls=source.get('calls', []),
                imports=source.get('imports', []),
                decorators=source.get('decorators', []),
                error_handling=source.get('error_handling', {}),
                line_numbers=source.get('line_numbers', []),
                file_name=source.get('file_name', ''),
                code_with_line_numbers=source.get('code_with_line_numbers', '')
            )
        except Exception as e:
            self.logger.error(f"Failed to build function metadata: {e}")
            return None

    def search_by_filters(self, filters: Dict[str, Any], limit: int = 10) -> List[SearchResult]:
        """Search functions by specific filters (file_path, repository_name, etc.)"""
        if not filters:
            return []
            
        filter_conditions = []
        for key, value in filters.items():
            if key in ['func_name', 'repository_name', 'module_name', 'class_context']:
                filter_conditions.append({"term": {key: value}})
            elif key == 'is_async':
                filter_conditions.append({"term": {key: bool(value)}})
            elif key in ['start_line', 'end_line']:
                filter_conditions.append({"range": {key: {"gte": value}}})
        
        if not filter_conditions:
            return []
        
        search_body = {
            "query": {
                "bool": {
                    "filter": filter_conditions
                }
            },
            "size": min(limit, MAX_FUNCTIONS_PER_SEARCH),
            "_source": {"excludes": ["embedding", "embedding_knn"]}
        }
        
        try:
            response = self.client.search(index=self.index_name, body=search_body)
        except RequestError as e:
            self.logger.error(f"OpenSearch request error during filter search: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Filter search failed: {e}")
            return []
        
        try:
            hits = response.get('hits', {}).get('hits', [])
            
            results = []
            for hit in hits:
                source = hit['_source']
                function_metadata = self._build_function_metadata(source)
                
                if function_metadata:
                    search_result = SearchResult(
                        function_metadata=function_metadata,
                        relevance_score=hit['_score'],
                        search_method="filter_search",
                        match_type="exact",
                        approach_used=AnalysisApproach.FUNCTION_LOOKUP_TABLE
                    )
                    results.append(search_result)
            
            return results
        except Exception as e:
            self.logger.error(f"Error processing filter search results: {e}")
            return []

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the search index"""
        try:
            if not self.client.indices.exists(index=self.index_name):
                return {'error': 'Index does not exist', 'index_name': self.index_name}
                
            stats = self.client.indices.stats(index=self.index_name)
            return {
                'document_count': stats['indices'][self.index_name]['total']['docs']['count'],
                'store_size': stats['indices'][self.index_name]['total']['store']['size_in_bytes'],
                'index_name': self.index_name,
                'embedding_dimensions': self.embedding_dimensions,
                'cluster_status': self.client.cluster.health().get('status', 'unknown')
            }
        except Exception as e:
            self.logger.error(f"Failed to get index stats: {e}")
            return {'error': str(e), 'index_name': self.index_name}
