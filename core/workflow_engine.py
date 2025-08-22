import os
import logging
from typing import List, Dict, Any
from factories.service_factory import ServiceFactory
from models.function_model import AnalysisRequest, AnalysisResult, SearchResult
from utils.history_manager import HistoryManager

class WorkflowEngine:
    def __init__(self, 
                 embedding_service_type: str = "openai",
                 llm_service_type: str = "openai"):
        self.service_factory = ServiceFactory()
        self.embedding_service_type = embedding_service_type
        self.llm_service_type = llm_service_type
        
        self.repo_processor = self.service_factory.get_repository_processor()
        self.lookup_table = self.service_factory.get_lookup_table()
        self.embedding_service = self.service_factory.get_embedding_service(embedding_service_type)
        self.search_service = self.service_factory.get_search_service(embedding_service_type)
        self.query_enhancer = self.service_factory.get_query_enhancer(llm_service_type)
        self.analysis_service = self.service_factory.get_analysis_service(llm_service_type)
        self.history_manager = HistoryManager()

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def process_repository(self, repo_path: str) -> Dict[str, Any]:
        if not os.path.exists(repo_path):
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        if not os.path.isdir(repo_path):
            raise ValueError(f"Path is not a directory: {repo_path}")
        
        self.logger.info(f"Processing repository: {repo_path}")
        
        try:
            functions = self.repo_processor.process_repository(repo_path)
        except Exception as e:
            self.logger.error(f"Error processing repository: {e}")
            raise
        
        self.search_service.setup_index()
        
        embedded_count = 0
        for function in functions:
            embedding = self.embedding_service.create_embedding(function)
            if embedding:
                function.embedding = embedding
                if self.search_service.store_function(function, embedding):
                    embedded_count += 1
            
            if embedded_count % 10 == 0:
                self.logger.info(f"Processed {embedded_count} functions")
        
        self.lookup_table.build_lookup_table(functions)
        
        self.logger.info(f"Repository processing complete: {embedded_count}/{len(functions)} functions embedded")
        
        return {
            "total_functions": len(functions),
            "embedded_functions": embedded_count,
            "summary": self.lookup_table.get_table_summary()
        }

    def analyze_user_issue(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        if not user_query or not user_query.strip():
            return {"error": "Query cannot be empty"}
        
        user_query = user_query.strip()
        context = context or {}
        
        self.logger.info(f"Analyzing user issue: {user_query[:50]}...")
        
        try:
            enhanced_query = self.query_enhancer.enhance_query(user_query, context)
        except Exception as e:
            self.logger.warning(f"Query enhancement failed: {e}")
            enhanced_query = user_query
        
        search_results = self.search_service.search_functions(enhanced_query, limit=5)
        
        if not search_results:
            return {
                "error": "No relevant functions found for the query",
                "query": user_query,
                "enhanced_query": enhanced_query
            }
        
        search_results = self._enhance_with_nested_functions(search_results)
        
        analysis_request = AnalysisRequest(
            query=user_query,
            enhanced_query=enhanced_query,
            functions=search_results,
            context=context or {}
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
            context=context
        )
        
        self.logger.info(f"Analysis complete with confidence: {analysis_result.confidence_score}")
        
        return {
            "query": user_query,
            "enhanced_query": enhanced_query,
            "functions_found": len(search_results),
            "analysis": analysis_result.analysis,
            "confidence_score": analysis_result.confidence_score,
            "functions_analyzed": analysis_result.functions_analyzed,
            "search_results": search_results
        }

    def _enhance_with_nested_functions(self, search_results: List[SearchResult]) -> List[SearchResult]:
        self.logger.info("Enhancing results with nested functions")
        
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
        self.logger.info("Starting iterative analysis")
        
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
                        match_type="additional_context"
                    )
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
    
    def get_analysis_history_stats(self) -> Dict[str, Any]:
        return self.history_manager.get_statistics()
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.history_manager.get_recent_analyses(limit)
    
    def export_function_lookup_table(self, filepath: str, format: str = "json"):
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
