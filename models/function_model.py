from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class AnalysisApproach(Enum):
    FUNCTION_LOOKUP_TABLE = "function_lookup_table"
    CALL_GRAPH = "call_graph"

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
    file_name: str = ""
    code_with_line_numbers: str = ""
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        if not self.file_name:
            self.file_name = self.file_path.split('/')[-1] if self.file_path else ""
        if not self.code_with_line_numbers and self.code:
            lines = self.code.split('\n')
            numbered_lines = []
            for i, line in enumerate(lines):
                numbered_lines.append(f"{self.start_line + i:4d}: {line}")
            self.code_with_line_numbers = '\n'.join(numbered_lines)

@dataclass
class SearchResult:
    function_metadata: FunctionMetadata
    relevance_score: float
    search_method: str
    match_type: str
    approach_used: AnalysisApproach = AnalysisApproach.FUNCTION_LOOKUP_TABLE
    nested_functions: Dict[str, Any] = None

@dataclass
class AnalysisRequest:
    query: str
    enhanced_query: str
    functions: List[SearchResult]
    context: Dict[str, Any]
    approach: AnalysisApproach = AnalysisApproach.FUNCTION_LOOKUP_TABLE
    call_graph_context: Dict[str, Any] = None

@dataclass
class AnalysisResult:
    analysis: str
    confidence_score: float
    functions_analyzed: int
    additional_context_needed: List[str]
    suggested_fixes: List[Dict[str, str]]
    approach_used: AnalysisApproach = AnalysisApproach.FUNCTION_LOOKUP_TABLE
    graph_context: Dict[str, Any] = None
