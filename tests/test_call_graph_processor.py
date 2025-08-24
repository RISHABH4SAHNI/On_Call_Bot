import pytest
from unittest.mock import Mock, patch
from core.call_graph_processor import CallGraphProcessor
from models.function_model import FunctionMetadata
from models.call_graph_model import CallGraph, CallGraphNode

class TestCallGraphProcessor:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.processor = CallGraphProcessor()
        
        # Create sample function metadata
        self.sample_functions = [
            FunctionMetadata(
                name="main_function",
                lookup_id="func-1",
                file_path="/src/main.py",
                repository_name="test-repo",
                module_name="src.main",
                start_line=10,
                end_line=20,
                code="def main_function(): pass",
                calls=["helper_function", "validator"]
            ),
            FunctionMetadata(
                name="helper_function", 
                lookup_id="func-2",
                file_path="/src/helpers.py",
                repository_name="test-repo",
                module_name="src.helpers",
                start_line=5,
                end_line=15,
                code="def helper_function(): pass",
                calls=["utility_function"]
            ),
            FunctionMetadata(
                name="utility_function",
                lookup_id="func-3", 
                file_path="/src/utils.py",
                repository_name="test-repo",
                module_name="src.utils",
                start_line=1,
                end_line=8,
                code="def utility_function(): pass",
                calls=[]
            ),
            FunctionMetadata(
                name="validator",
                lookup_id="func-4",
                file_path="/src/validators.py", 
                repository_name="test-repo",
                module_name="src.validators",
                start_line=15,
                end_line=25,
                code="def validator(): pass",
                calls=[]
            )
        ]
    
    def test_processor_initialization(self):
        """Test call graph processor initializes correctly"""
        assert self.processor.call_graph is None
        assert isinstance(self.processor.function_map, dict)
        assert len(self.processor.function_map) == 0
    
    def test_build_call_graph(self):
        """Test call graph construction"""
        call_graph = self.processor.build_call_graph(self.sample_functions)
        
        assert isinstance(call_graph, CallGraph)
        assert len(call_graph.nodes) == 4
        assert len(call_graph.edges) > 0
        
        # Check nodes are created correctly
        node_names = [node.function_metadata.name for node in call_graph.nodes.values()]
        expected_names = ["main_function", "helper_function", "utility_function", "validator"]
        for name in expected_names:
            assert name in node_names
    
    def test_build_edges(self):
        """Test edge construction between functions"""
        self.processor.build_call_graph(self.sample_functions)
        
        # Check main_function calls helper_function and validator
        main_node = None
        for node in self.processor.call_graph.nodes.values():
            if node.function_metadata.name == "main_function":
                main_node = node
                break
                
        assert main_node is not None
        assert len(main_node.calls) == 2  # helper_function and validator
        
        called_names = [called_node.function_metadata.name for called_node in main_node.calls]
        assert "helper_function" in called_names
        assert "validator" in called_names
    
    def test_identify_root_and_leaf_nodes(self):
        """Test identification of root and leaf nodes"""
        self.processor.build_call_graph(self.sample_functions)
        
        # main_function should be root (no incoming edges)
        root_nodes = [node.function_metadata.name for node in self.processor.call_graph.root_nodes]
        assert "main_function" in root_nodes
        
        # utility_function and validator should be leaf nodes (no outgoing edges)
        leaf_nodes = [node.function_metadata.name for node in self.processor.call_graph.leaf_nodes]
        assert "utility_function" in leaf_nodes
        assert "validator" in leaf_nodes
    
    def test_get_function_context_with_dependencies(self):
        """Test getting function context with dependencies"""
        self.processor.build_call_graph(self.sample_functions)
        
        # Get context for helper_function
        context = self.processor.get_function_context_with_dependencies("func-2", depth=2)
        
        assert "target_function" in context
        assert "called_functions" in context
        assert "calling_functions" in context
        assert context["target_function"]["name"] == "helper_function"
        
        # Should include utility_function as called
        called_names = [f["name"] for f in context["called_functions"]]
        assert "utility_function" in called_names
        
        # Should include main_function as caller
        calling_names = [f["name"] for f in context["calling_functions"]]
        assert "main_function" in calling_names
    
    def test_find_functions_by_name(self):
        """Test finding functions by name"""
        self.processor.build_call_graph(self.sample_functions)
        
        results = self.processor.find_functions_by_name("helper_function")
        assert len(results) == 1
        assert results[0].function_metadata.name == "helper_function"
        
        # Test partial matching
        results = self.processor.find_functions_by_name("helper")
        assert len(results) == 1
        
        # Test no matches
        results = self.processor.find_functions_by_name("nonexistent")
        assert len(results) == 0
    
    def test_get_call_paths_to_function(self):
        """Test getting call paths to a function"""
        self.processor.build_call_graph(self.sample_functions)
        
        paths = self.processor.get_call_paths_to_function("func-3", max_depth=3)  # utility_function
        
        assert len(paths) > 0
        # Should find path: main_function -> helper_function -> utility_function
        path_names = []
        for path in paths:
            path_function_names = []
            for func_id in path:
                node = self.processor.call_graph.nodes[func_id]
                path_function_names.append(node.function_metadata.name)
            path_names.append(path_function_names)
        
        expected_path = ["main_function", "helper_function", "utility_function"]
        assert expected_path in path_names
    
    def test_get_graph_statistics(self):
        """Test graph statistics calculation"""
        self.processor.build_call_graph(self.sample_functions)
        
        stats = self.processor.get_graph_statistics()
        
        assert stats["total_nodes"] == 4
        assert stats["total_edges"] == 3  # main->helper, main->validator, helper->utility
        assert stats["root_nodes"] == 1   # main_function
        assert stats["leaf_nodes"] == 2   # utility_function, validator
        assert "max_depth" in stats
        assert "avg_calls_per_function" in stats
    
    def test_empty_functions_list(self):
        """Test handling empty functions list"""
        call_graph = self.processor.build_call_graph([])
        
        assert isinstance(call_graph, CallGraph)
        assert len(call_graph.nodes) == 0
        assert len(call_graph.edges) == 0
        assert len(call_graph.root_nodes) == 0
        assert len(call_graph.leaf_nodes) == 0
    
    def test_single_function(self):
        """Test handling single function with no calls"""
        single_function = [self.sample_functions[2]]  # utility_function with no calls
        
        call_graph = self.processor.build_call_graph(single_function)
        
        assert len(call_graph.nodes) == 1
        assert len(call_graph.edges) == 0
        assert len(call_graph.root_nodes) == 1
        assert len(call_graph.leaf_nodes) == 1
        
        node = list(call_graph.nodes.values())[0]
        assert node.function_metadata.name == "utility_function"
