import os
import logging
from typing import List, Dict, Any
from factories.service_factory import ServiceFactory
from models.function_model import AnalysisRequest, AnalysisResult, SearchResult, AnalysisApproach
from utils.history_manager import HistoryManager
from config.settings import SUPPORTED_APPROACHES, DEFAULT_ANALYSIS_APPROACH, MAX_CALL_GRAPH_DEPTH

class WorkflowEngine:
    def __init__(self, 
                 embedding_service_type: str = "openai",
                 llm_service_type: str = "openai",
                 analysis_approach: str = DEFAULT_ANALYSIS_APPROACH):
        self.service_factory = ServiceFactory()
        self.embedding_service_type = embedding_service_type
        self.llm_service_type = llm_service_type
        self.analysis_approach = analysis_approach
        
        if not self.service_factory.validate_approach(analysis_approach):
            raise ValueError(f"Unsupported analysis approach: {analysis_approach}. Supported: {SUPPORTED_APPROACHES}")
        
        self.services = self.service_factory.get_services_for_approach(
            analysis_approach, embedding_service_type, llm_service_type
        )
        
        self.repo_processor = self.services['repository_processor']
        self.embedding_service = self.services['embedding_service']
        self.search_service = self.services['search_service']
        self.query_enhancer = self.services['query_enhancer']
        self.analysis_service = self.services['analysis_service']
        
        if analysis_approach == "call_graph":
            self.call_graph_processor = self.services['call_graph_processor']
            self.lookup_table = None
        else:
            self.lookup_table = self.services['lookup_table']
            self.call_graph_processor = None
        
        self.history_manager = HistoryManager()

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"WorkflowEngine initialized with approach: {analysis_approach}")

    def process_repository(self, repo_path: str) -> Dict[str, Any]:
        if not os.path.exists(repo_path):
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        if not os.path.isdir(repo_path):
            raise ValueError(f"Path is not a directory: {repo_path}")
        
        self.logger.info(f"Processing repository: {repo_path} using {self.analysis_approach} approach")
        
        try:
            functions = self.repo_processor.process_repository(repo_path)
        except Exception as e:
            self.logger.error(f"Error processing repository: {e}")
            raise
        
        if self.analysis_approach == "call_graph":
            return self._process_with_call_graph(functions)
        else:
            return self._process_with_lookup_table(functions)
    
    def _process_with_call_graph(self, functions: List) -> Dict[str, Any]:
        self.logger.info("Processing with call graph approach")
        
        self.search_service.setup_index()
        
        graph_stats = self.search_service.build_and_store_call_graph(functions)
        
        self.logger.info(f"Call graph processing complete: {graph_stats}")
        
        return {
            "total_functions": graph_stats.get('total_functions', len(functions)),
            "embedded_functions": graph_stats.get('stored_functions', 0),
            "approach": "call_graph",
            "graph_statistics": graph_stats,
            "summary": self._get_call_graph_summary(graph_stats)
        }
    
    def _process_with_lookup_table(self, functions: List) -> Dict[str, Any]:
        self.logger.info("Processing with function lookup table approach")
        
        self.search_service.setup_index()
        
        embedded_count = 0
        for function in functions:
            embedding = self.embedding_service.create_embedding(function, include_metadata=True)
            if embedding:
                function.embedding = embedding
                if self.search_service.store_function(function, embedding):
                    embedded_count += 1
            
            if embedded_count % 10 == 0:
                self.logger.info(f"Processed {embedded_count} functions")
        
        self.lookup_table.build_lookup_table(functions)
        
        self.logger.info(f"Lookup table processing complete: {embedded_count}/{len(functions)} functions embedded")
        
        return {
            "total_functions": len(functions),
            "embedded_functions": embedded_count,
            "approach": "function_lookup_table",
            "summary": self.lookup_table.get_table_summary()
        }

    def analyze_user_issue(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        if not user_query or not user_query.strip():
            return {"error": "Query cannot be empty"}
        
        user_query = user_query.strip()
        context = context or {}
        
        self.logger.info(f"Analyzing user issue with {self.analysis_approach}: {user_query[:50]}...")
        
        try:
            enhanced_query = self.query_enhancer.enhance_query(user_query, context)
        except Exception as e:
            self.logger.warning(f"Query enhancement failed: {e}")
            enhanced_query = user_query
        
        if self.analysis_approach == "call_graph":
            search_results = self._search_with_call_graph(enhanced_query, context)
        else:
            search_results = self._search_with_lookup_table(enhanced_query)
        
        if not search_results:
            return {
                "error": "No relevant functions found for the query",
                "query": user_query,
                "enhanced_query": enhanced_query,
                "approach": self.analysis_approach
            }
        
        if self.analysis_approach == "function_lookup_table":
            search_results = self._enhance_with_nested_functions(search_results)
        
        analysis_request = AnalysisRequest(
            query=user_query,
            enhanced_query=enhanced_query,
            functions=search_results,
            context=context or {},
            approach=AnalysisApproach.CALL_GRAPH if self.analysis_approach == "call_graph" else AnalysisApproach.FUNCTION_LOOKUP_TABLE,
            call_graph_context=self._get_call_graph_context(search_results) if self.analysis_approach == "call_graph" else None
        )
        
        analysis_result = self._perform_iterative_analysis(analysis_request)
        
        self.history_manager.add_analysis(
            query=user_query,
            enhanced_query=enhanced_query,
            analysis_result=analysis_result.analysis,
            confidence_score=analysis_result.confidence_score,
            functions_analyzed=analysis_result.functions_analyzed,
            embedding_service=self.embedding_service_type,
            llm_service=self.llm_service_type,
            context={**context, "approach": self.analysis_approach}
        )
        
        self.logger.info(f"Analysis complete with confidence: {analysis_result.confidence_score} using {self.analysis_approach}")
        
        return {
            "query": user_query,
            "enhanced_query": enhanced_query,
            "functions_found": len(search_results),
            "analysis": analysis_result.analysis,
            "confidence_score": analysis_result.confidence_score,
            "functions_analyzed": analysis_result.functions_analyzed,
            "search_results": search_results,
            "approach": self.analysis_approach,
            "graph_context": analysis_result.graph_context if hasattr(analysis_result, 'graph_context') else None
        }
    
    def _search_with_call_graph(self, query: str, context: Dict[str, Any]) -> List[SearchResult]:
        max_depth = context.get('call_graph_depth', MAX_CALL_GRAPH_DEPTH)
        return self.search_service.search_functions_with_context(query, limit=5, max_depth=max_depth)
    
    def _search_with_lookup_table(self, query: str) -> List[SearchResult]:
        return self.search_service.search_functions(query, limit=5)
    
    def _get_call_graph_context(self, search_results: List[SearchResult]) -> Dict[str, Any]:
        if not search_results or self.analysis_approach != "call_graph":
            return {}
        
        context = {
            "total_functions": len(search_results),
            "functions_with_dependencies": 0,
            "max_depth": 0,
            "total_dependencies": 0
        }
        
        for result in search_results:
            if result.nested_functions and 'call_graph_context' in result.nested_functions:
                graph_ctx = result.nested_functions['call_graph_context']
                context["functions_with_dependencies"] += 1
                context["max_depth"] = max(context["max_depth"], graph_ctx.get('graph_depth', 0))
                context["total_dependencies"] += graph_ctx.get('dependency_count', 0)
        
        return context

    def _enhance_with_nested_functions(self, search_results: List[SearchResult]) -> List[SearchResult]:
        if self.analysis_approach != "function_lookup_table":
            return search_results
            
        self.logger.info("Enhancing results with nested functions (lookup table approach)")
        
        for result in search_results:
            nested_functions = {}
            for nested_id in result.function_metadata.nested_call_ids:
                nested_func = self.search_service.get_function_by_id(nested_id)
                if nested_func:
                    nested_functions[nested_id] = {
                        "function_name": nested_func.name,
                        "file_path": nested_func.file_path,
                        "code": nested_func.code,
                        "start_line": nested_func.start_line,
                        "end_line": nested_func.end_line
                    }
            result.nested_functions = nested_functions
        return search_results

    def _perform_iterative_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        self.logger.info(f"Starting iterative analysis with {self.analysis_approach} approach")
        
        analysis_result = self.analysis_service.analyze_issue(request)
        
        self.logger.info(f"Initial confidence: {analysis_result.confidence_score}")
        
        max_iterations = 3
        current_iteration = 0
        
        while (analysis_result.confidence_score < 0.8 and 
               analysis_result.additional_context_needed and 
               current_iteration < max_iterations):
            
            self.logger.info(f"Requesting additional context (iteration {current_iteration + 1})")
            
            additional_functions = []
            for function_id in analysis_result.additional_context_needed:
                func = self.search_service.get_function_by_id(function_id)
                if func:
                    search_result = SearchResult(
                        function_metadata=func,
                        relevance_score=1.0,
                        search_method="context_request",
                        match_type="additional_context",
                        approach_used=AnalysisApproach.CALL_GRAPH if self.analysis_approach == "call_graph" else AnalysisApproach.FUNCTION_LOOKUP_TABLE
                    )
                    
                    if self.analysis_approach == "call_graph":
                        graph_result = self.search_service.get_function_with_graph_context(function_id)
                        if graph_result:
                            search_result.nested_functions = {
                                'call_graph_context': graph_result.get_context_summary(),
                                'dependency_functions': [node.function_metadata.lookup_id for node in graph_result.dependency_context]
                            }
                    
                    additional_functions.append(search_result)
            
            if additional_functions:
                request.functions.extend(additional_functions)
                analysis_result = self.analysis_service.analyze_issue(request)
                self.logger.info(f"Updated confidence after iteration {current_iteration + 1}: {analysis_result.confidence_score}")
            else:
                self.logger.info("No additional functions found, stopping iterations")
                break
            
            current_iteration += 1
        
        return analysis_result
    
    def _get_call_graph_summary(self, graph_stats: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'total_nodes': graph_stats.get('total_nodes', 0),
            'root_nodes': graph_stats.get('root_nodes', 0),
            'leaf_nodes': graph_stats.get('leaf_nodes', 0),
            'max_depth': graph_stats.get('max_depth', 0),
            'total_edges': graph_stats.get('total_edges', 0),
            'stored_functions': graph_stats.get('stored_functions', 0),
            'approach': 'call_graph'
        }
    
    def switch_analysis_approach(self, new_approach: str):
        if not self.service_factory.validate_approach(new_approach):
            raise ValueError(f"Unsupported analysis approach: {new_approach}")
        
        if new_approach == self.analysis_approach:
            self.logger.info(f"Already using {new_approach} approach")
            return
        
        self.logger.info(f"Switching from {self.analysis_approach} to {new_approach}")
        
        self.analysis_approach = new_approach
        
        self.services = self.service_factory.get_services_for_approach(
            new_approach, self.embedding_service_type, self.llm_service_type
        )
        
        self.search_service = self.services['search_service']
        
        if new_approach == "call_graph":
            self.call_graph_processor = self.services['call_graph_processor']
            self.lookup_table = None
        else:
            self.lookup_table = self.services['lookup_table']
            self.call_graph_processor = None
    
    def get_analysis_history_stats(self) -> Dict[str, Any]:
        stats = self.history_manager.get_statistics()
        stats['current_approach'] = self.analysis_approach
        return stats
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.history_manager.get_recent_analyses(limit)
    
    def export_function_lookup_table(self, filepath: str, format: str = "json"):
        if self.analysis_approach == "call_graph":
            raise ValueError("Function lookup table export not available for call graph approach")
            
        if format.lower() == "json":
            self.lookup_table.export_to_json(filepath)
        elif format.lower() == "csv":
            self.lookup_table.export_to_csv(filepath)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'csv'")
        
        self.logger.info(f"Function lookup table exported to {filepath}")
    
    def validate_services(self) -> Dict[str, bool]:
        validation_results = {
            "embedding_service": False,
            "search_service": False,
            "query_enhancer": False,
            "analysis_service": False
        }
        
        try:
            test_embedding = self.embedding_service.create_query_embedding("test")
            validation_results["embedding_service"] = test_embedding is not None
        except:
            pass
        
        try:
            enhanced = self.query_enhancer.enhance_query("test")
            validation_results["query_enhancer"] = enhanced is not None
        except:
            pass
        
        validation_results["search_service"] = True
        validation_results["analysis_service"] = True
        
        return validation_results
    
    def get_supported_approaches(self):
        return self.service_factory.get_supported_approaches()
