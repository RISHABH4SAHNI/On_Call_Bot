import logging
import os
from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch
from opensearchpy.connection import RequestsHttpConnection
from models.function_model import FunctionMetadata, SearchResult, AnalysisApproach
from models.call_graph_model import CallGraphSearchResult, CallGraphNode
from services.embedding_service import EmbeddingService
from core.call_graph_processor import CallGraphProcessor
from config.settings import get_opensearch_config, CALL_GRAPH_CONFIG, MAX_FUNCTIONS_PER_SEARCH

class CallGraphSearchService:
    def __init__(self, embedding_service: EmbeddingService):
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
        self.index_name = CALL_GRAPH_CONFIG['index_name']
        self.call_graph_processor = CallGraphProcessor()
        self.functions_by_id: Dict[str, FunctionMetadata] = {}
        self.call_graph = None
        self.logger = logging.getLogger(__name__)

    def setup_index(self):
        try:
            if not self.client.indices.exists(index=self.index_name):
                index_config = {
                    "settings": CALL_GRAPH_CONFIG['settings'],
                    "mappings": CALL_GRAPH_CONFIG['mappings']
                }
                self.client.indices.create(index=self.index_name, body=index_config)
                self.logger.info(f"Created call graph index: {self.index_name}")
            else:
                self.logger.debug(f"Call graph index {self.index_name} already exists")
        except Exception as e:
            self.logger.error(f"Failed to setup call graph index: {e}")
            raise

    def build_and_store_call_graph(self, functions: List[FunctionMetadata]) -> Dict[str, Any]:
        if not functions:
            self.logger.warning("No functions provided for call graph building")
            return {"error": "No functions provided", "stored_functions": 0, "total_functions": 0}
            
        self.functions_by_id = {func.lookup_id: func for func in functions}
        
        try:
            self.call_graph = self.call_graph_processor.build_call_graph(functions)
            self.logger.info(f"Built call graph with {len(self.call_graph.nodes)} nodes")
        except Exception as e:
            self.logger.error(f"Failed to build call graph: {e}")
            return {"error": f"Call graph building failed: {e}", "stored_functions": 0, "total_functions": len(functions)}
        
        stored_count = 0
        failed_functions = []
        
        for function in functions:
            try:
                embedding = self.embedding_service.create_call_graph_embedding(function)
                if embedding and len(embedding) == 3072:
                    function.embedding = embedding
                    if self.store_function_with_graph_context(function):
                        stored_count += 1
                    else:
                        failed_functions.append(function.name)
                else:
                    self.logger.warning(f"Invalid embedding for function {function.name}")
                    failed_functions.append(function.name)
            except Exception as e:
                self.logger.error(f"Failed to process function {function.name}: {e}")
                failed_functions.append(function.name)
        
        stats = self.call_graph_processor.get_graph_statistics()
        stats['stored_functions'] = stored_count
        stats['total_functions'] = len(functions)
        stats['failed_functions'] = len(failed_functions)
        
        if failed_functions:
            self.logger.warning(f"Failed to store {len(failed_functions)} functions: {failed_functions[:5]}...")
        
        return stats
    def store_function_with_graph_context(self, function: FunctionMetadata) -> bool:
        if not self.call_graph:
            self.logger.error("Call graph not initialized")
            return False
            
        node = self.call_graph.get_node(function.lookup_id)
        if not node:
            self.logger.warning(f"Node not found in call graph for function {function.name}")
            return False
            
        if not function.embedding:
            self.logger.warning(f"No embedding available for function {function.name}")
            return False
        
        doc = {
            "embedding": function.embedding,
            "embedding_knn": function.embedding,
            "func_name": function.name,
            "lookup_id": function.lookup_id,
            "file_path": function.file_path,
            "file_name": function.file_name or function.file_path.split('/')[-1],
            "repository_name": function.repository_name,
            "module_name": function.module_name,
            "code_with_line_numbers": function.code_with_line_numbers,
            "start_line": function.start_line,
            "end_line": function.end_line,
            "is_async": function.is_async,
            "class_context": function.class_context,
            "has_error_handling": function.error_handling.get('has_try_catch', False),
            "depth_level": node.depth_level,
            "dependencies_count": len(node.dependencies),
            "dependents_count": len(node.dependents),
            "decorators": function.decorators
        }
        
        try:
            self.client.index(index=self.index_name, id=function.lookup_id, body=doc)
            self.logger.debug(f"Stored function with graph context: {function.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store function {function.name} with graph context: {e}")
            return False

    def search_functions_with_context(self, query: str, limit: int = 5, max_depth: int = 3) -> List[SearchResult]:
        if not query or not query.strip():
            self.logger.warning("Empty query provided to call graph search")
            return []
            
        # Validate and cap limit
        limit = min(max(1, limit), MAX_FUNCTIONS_PER_SEARCH)
        max_depth = min(max(1, max_depth), CALL_GRAPH_CONFIG['max_depth'])
        
        query_embedding = self.embedding_service.create_query_embedding(query)
        if not query_embedding:
            self.logger.warning("Failed to create query embedding for call graph search")
            return []
            
        # Validate embedding dimensions
        if len(query_embedding) != 3072:
            self.logger.error(f"Invalid query embedding dimensions: {len(query_embedding)}")
            return []

        search_body = {
            "query": {
                "knn": {
                    "embedding_knn": {
                        "vector": query_embedding,
                        "k": min(limit * 2, 100)
                    }
                }
            },
            "size": limit,
            "_source": {
                "excludes": ["embedding", "embedding_knn"]
            }
        }

        try:
            response = self.client.search(index=self.index_name, body=search_body)
            hits = response.get('hits', {}).get('hits', [])
            
            if not hits:
                self.logger.info(f"No call graph search results found for query: {query[:50]}...")
                return []
            
            results = []
            for hit in hits:
                source = hit['_source']
                function_metadata = self._build_function_metadata(source)
                
                if not function_metadata:
                    continue
                
                try:
                    call_graph_result = self.call_graph_processor.get_function_context_with_dependencies(
                        function_metadata.lookup_id, max_depth
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to get call graph context for {function_metadata.name}: {e}")
                    call_graph_result = None
                
                search_result = SearchResult(
                    function_metadata=function_metadata,
                    relevance_score=hit['_score'],
                    search_method="call_graph_vector_similarity",
                    match_type="semantic_with_graph_context",
                    approach_used=AnalysisApproach.CALL_GRAPH
                )
                
                if call_graph_result:
                    try:
                        search_result.nested_functions = {
                            'call_graph_context': call_graph_result.get_context_summary(),
                            'dependency_functions': [node.function_metadata.lookup_id for node in call_graph_result.dependency_context] if call_graph_result.dependency_context else [],
                            'call_paths': call_graph_result.call_paths if hasattr(call_graph_result, 'call_paths') else []
                        }
                    except Exception as e:
                        self.logger.warning(f"Failed to build nested functions context: {e}")
                        search_result.nested_functions = {}
                else:
                    search_result.nested_functions = {}
                
                results.append(search_result)
            
            self.logger.info(f"Found {len(results)} call graph search results")
            return results
        except Exception as e:
            self.logger.error(f"Call graph search failed: {e}")
            return []

    def get_function_by_id(self, lookup_id: str) -> Optional[FunctionMetadata]:
        if not lookup_id:
            return None
        return self.functions_by_id.get(lookup_id)

    def get_function_with_graph_context(self, lookup_id: str, max_depth: int = 3) -> Optional[CallGraphSearchResult]:
        if not lookup_id or not self.call_graph_processor:
            return None
        try:
            return self.call_graph_processor.get_function_context_with_dependencies(lookup_id, max_depth)
        except Exception as e:
            self.logger.error(f"Failed to get function with graph context: {e}")
            return None

    def _build_function_metadata(self, source: Dict[str, Any]) -> FunctionMetadata:
        try:
            lookup_id = source['lookup_id']
            if lookup_id in self.functions_by_id:
                return self.functions_by_id[lookup_id]
        
            # Build from search source if not in cache
            return FunctionMetadata(
                    name=source.get('func_name', ''),
                lookup_id=lookup_id,
                    file_path=source.get('file_path', ''),
                    repository_name=source.get('repository_name', ''),
                    module_name=source.get('module_name', ''),
                nested_call_ids=[],
                    start_line=source.get('start_line', 0),
                    end_line=source.get('end_line', 0),
                code="",
                    is_async=source.get('is_async', False),
                class_context=source.get('class_context'),
                calls=[],
                imports=[],
                    decorators=source.get('decorators', []),
                error_handling={'has_try_catch': source.get('has_error_handling', False)},
                    line_numbers=list(range(source.get('start_line', 0), source.get('end_line', 0) + 1)),
                file_name=source.get('file_name', ''),
                code_with_line_numbers=source.get('code_with_line_numbers', '')
            )
        except Exception as e:
            self.logger.error(f"Failed to build function metadata: {e}")
            return None
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the call graph search index"""
        try:
            stats = self.client.indices.stats(index=self.index_name)
            return {
                'document_count': stats['indices'][self.index_name]['total']['docs']['count'],
                'store_size': stats['indices'][self.index_name]['total']['store']['size_in_bytes'],
                'index_name': self.index_name
            }
        except Exception as e:
            self.logger.error(f"Failed to get call graph index stats: {e}")
            return {}

