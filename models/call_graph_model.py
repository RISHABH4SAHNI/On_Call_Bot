from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from models.function_model import FunctionMetadata

@dataclass
class CallGraphNode:
    function_metadata: FunctionMetadata
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    depth_level: int = 0
    visited: bool = False
    
@dataclass
class CallGraph:
    nodes: Dict[str, CallGraphNode] = field(default_factory=dict)
    root_nodes: Set[str] = field(default_factory=set)
    leaf_nodes: Set[str] = field(default_factory=set)
    max_depth: int = 0
    
    def add_node(self, function: FunctionMetadata) -> CallGraphNode:
        node = CallGraphNode(function_metadata=function)
        self.nodes[function.lookup_id] = node
        return node
    
    def add_edge(self, caller_id: str, callee_id: str):
        if caller_id in self.nodes and callee_id in self.nodes:
            self.nodes[caller_id].dependencies.add(callee_id)
            self.nodes[callee_id].dependents.add(caller_id)
    
    def get_node(self, lookup_id: str) -> Optional[CallGraphNode]:
        return self.nodes.get(lookup_id)
    
    def get_dependencies_dfs(self, node_id: str, max_depth: int = 3) -> List[CallGraphNode]:
        if node_id not in self.nodes:
            return []
        
        visited = set()
        result = []
        
        def dfs(current_id: str, depth: int):
            if depth > max_depth or current_id in visited:
                return
            visited.add(current_id)
            node = self.nodes[current_id]
            result.append(node)
            for dep_id in node.dependencies:
                dfs(dep_id, depth + 1)
        
        dfs(node_id, 0)
        return result
    
    def calculate_depths(self):
        for node_id in self.root_nodes:
            self._calculate_depth_recursive(node_id, 0)
    
    def _calculate_depth_recursive(self, node_id: str, depth: int):
        if node_id not in self.nodes:
            return
        node = self.nodes[node_id]
        if depth > node.depth_level:
            node.depth_level = depth
            self.max_depth = max(self.max_depth, depth)
        for dep_id in node.dependencies:
            self._calculate_depth_recursive(dep_id, depth + 1)

@dataclass
class CallGraphSearchResult:
    primary_node: CallGraphNode
    dependency_context: List[CallGraphNode]
    relevance_score: float
    search_method: str
    graph_depth: int
    total_context_functions: int
    call_paths: List[List[str]] = field(default_factory=list)
    
    def get_all_functions(self) -> List[FunctionMetadata]:
        functions = [self.primary_node.function_metadata]
        for dep_node in self.dependency_context:
            if dep_node.function_metadata.lookup_id != self.primary_node.function_metadata.lookup_id:
                functions.append(dep_node.function_metadata)
        return functions
    
    def get_context_summary(self) -> Dict[str, Any]:
        return {
            'primary_function': self.primary_node.function_metadata.name,
            'dependency_count': len(self.dependency_context),
            'graph_depth': self.graph_depth,
            'total_functions': self.total_context_functions,
            'call_paths_count': len(self.call_paths),
            'relevance_score': self.relevance_score,
            'files_involved': list(set(func.file_name for func in self.get_all_functions())),
            'modules_involved': list(set(func.module_name for func in self.get_all_functions())),
            'has_error_handling': any(func.error_handling.get('has_try_catch', False) for func in self.get_all_functions()),
            'async_functions': sum(1 for func in self.get_all_functions() if func.is_async)
        }
