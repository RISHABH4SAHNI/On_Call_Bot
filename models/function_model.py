from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class FunctionMetadata:
    name: str
    lookup_id: str
    file_path: str
    repository_name: str
    module_name: str
    nested_call_ids: List[str]
    start_line: int
    end_line: int
    code: str
    is_async: bool
    class_context: Optional[str]
    calls: List[str]
    imports: List[str]
    decorators: List[str]
    error_handling: Dict[str, Any]
    line_numbers: List[int]
    embedding: Optional[List[float]] = None

@dataclass
class SearchResult:
    function_metadata: FunctionMetadata
    relevance_score: float
    search_method: str
    match_type: str
    nested_functions: Dict[str, Any] = None

@dataclass
class AnalysisRequest:
    query: str
    enhanced_query: str
    functions: List[SearchResult]
    context: Dict[str, Any]

@dataclass
class AnalysisResult:
    analysis: str
    confidence_score: float
    functions_analyzed: int
    additional_context_needed: List[str]
    suggested_fixes: List[Dict[str, str]]
