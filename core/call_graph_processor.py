from typing import List, Dict, Set, Optional
from models.function_model import FunctionMetadata
from models.call_graph_model import CallGraph, CallGraphNode, CallGraphSearchResult

class CallGraphProcessor:
    def __init__(self):
        self.call_graph: Optional[CallGraph] = None
        self.function_name_to_ids: Dict[str, Set[str]] = {}
        self.builtin_functions = {
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray', 'bytes',
            'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir',
            'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float', 'format', 'frozenset',
            'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int',
            'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
            'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'print',
            'property', 'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice',
            'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'
        }
    
    def build_call_graph(self, functions: List[FunctionMetadata]) -> CallGraph:
        self.call_graph = CallGraph()
        self.function_name_to_ids = {}
        
        for function in functions:
            self.call_graph.add_node(function)
            
            if function.name not in self.function_name_to_ids:
                self.function_name_to_ids[function.name] = set()
            self.function_name_to_ids[function.name].add(function.lookup_id)
        
        self._build_edges(functions)
        self._identify_root_and_leaf_nodes()
        self.call_graph.calculate_depths()
        
        return self.call_graph
    
    def _build_edges(self, functions: List[FunctionMetadata]):
        for function in functions:
            for call_name in function.calls:
                if call_name not in self.builtin_functions and call_name in self.function_name_to_ids:
                    for callee_id in self.function_name_to_ids[call_name]:
                        if callee_id != function.lookup_id:
                            self.call_graph.add_edge(function.lookup_id, callee_id)
    
    def _identify_root_and_leaf_nodes(self):
        for node_id, node in self.call_graph.nodes.items():
            if not node.dependents:
                self.call_graph.root_nodes.add(node_id)
            if not node.dependencies:
                self.call_graph.leaf_nodes.add(node_id)
    
    def get_function_context_with_dependencies(self, 
                                             target_function_id: str, 
                                             max_depth: int = 3) -> Optional[CallGraphSearchResult]:
        if not self.call_graph or target_function_id not in self.call_graph.nodes:
            return None
        
        primary_node = self.call_graph.nodes[target_function_id]
        dependency_context = self.call_graph.get_dependencies_dfs(target_function_id, max_depth)
        call_paths = self.get_call_paths_to_function(target_function_id, max_depth)
        
        return CallGraphSearchResult(
            primary_node=primary_node,
            dependency_context=dependency_context,
            relevance_score=1.0,
            search_method="call_graph_dfs",
            graph_depth=len(dependency_context),
            total_context_functions=len(dependency_context),
            call_paths=call_paths
        )
    
    def find_functions_by_name(self, function_name: str) -> List[CallGraphNode]:
        if not self.call_graph:
            return []
        
        result = []
        if function_name in self.function_name_to_ids:
            for lookup_id in self.function_name_to_ids[function_name]:
                if lookup_id in self.call_graph.nodes:
                    result.append(self.call_graph.nodes[lookup_id])
        return result
    
    def get_call_paths_to_function(self, target_function_id: str, max_depth: int = 3) -> List[List[str]]:
        if not self.call_graph or target_function_id not in self.call_graph.nodes:
            return []
        
        paths = []
        visited = set()
        
        def dfs_paths(current_id: str, path: List[str], depth: int):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            path.append(current_id)
            
            if current_id == target_function_id:
                paths.append(path.copy())
            else:
                node = self.call_graph.nodes[current_id]
                for dep_id in node.dependencies:
                    dfs_paths(dep_id, path, depth + 1)
            
            path.pop()
            visited.remove(current_id)
        
        for root_id in self.call_graph.root_nodes:
            dfs_paths(root_id, [], 0)
        
        return paths
    
    def get_graph_statistics(self) -> Dict[str, int]:
        if not self.call_graph:
            return {}
        
        return {
            'total_nodes': len(self.call_graph.nodes),
            'root_nodes': len(self.call_graph.root_nodes),
            'leaf_nodes': len(self.call_graph.leaf_nodes),
            'max_depth': self.call_graph.max_depth,
            'total_edges': sum(len(node.dependencies) for node in self.call_graph.nodes.values())
        }
    