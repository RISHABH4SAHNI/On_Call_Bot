# API Documentation

Programmatic API for the Code Analysis Bot system.

## Core Classes

### WorkflowEngine

Main orchestrator for repository processing and issue analysis.

```python
from core.workflow_engine import WorkflowEngine

engine = WorkflowEngine(
    embedding_service_type="openai",  # "openai", "ollama", "perplexity"
    llm_service_type="openai",        # "openai", "perplexity", "ollama"
    analysis_approach="call_graph"    # "function_lookup_table", "call_graph"
)
```

{
    "total_functions": 150,
    "embedded_functions": 148,
    "approach": "call_graph",
    "graph_statistics": {
        "total_nodes": 150,
        "root_nodes": 12,
        "leaf_nodes": 45,
        "max_depth": 4,
        "total_edges": 287
    },
    "summary": {
        "stored_functions": 148,
        "failed_functions": 2
    }
}
```
    "enhanced_query": "Authentication function JWT token validation errors...",
    "functions_found": 5,
    "analysis": "Detailed technical analysis...",
    "approach": "call_graph",
    "confidence_score": 0.85,
    "functions_analyzed": 5,
    "search_results": [...]
nested = lookup.get_nested_functions("func-uuid-123")
```

### CallGraphProcessor

Process and analyze function call relationships using graph theory.

```python
from core.call_graph_processor import CallGraphProcessor

processor = CallGraphProcessor()
call_graph = processor.build_call_graph(functions)
```

#### Methods

##### `build_call_graph(functions: List[FunctionMetadata]) -> CallGraph`

Build a complete call graph from function metadata.

```python
call_graph = processor.build_call_graph(functions)

# Returns CallGraph object with nodes, edges, and hierarchy
```

##### `get_function_context_with_dependencies(target_function_id: str, max_depth: int = 3) -> CallGraphSearchResult`

Get a function with its dependency context.

```python
context = processor.get_function_context_with_dependencies("func-uuid-123", max_depth=3)

# Returns:
# - Primary function node
# - All dependency functions (up to max_depth)
# - Call paths to the function
# - Graph statistics
```

##### `get_graph_statistics() -> Dict[str, int]`

Get call graph statistics.

```python
stats = processor.get_graph_statistics()

# Returns:
{
    "total_nodes": 150,
    "root_nodes": 12,      # Functions with no callers
    "leaf_nodes": 45,      # Functions that call no others
    "max_depth": 4,        # Maximum call chain depth
    "total_edges": 287     # Total function call relationships
}
```

### CallGraphSearchService

Vector similarity search enhanced with call graph context.

```python
from services.call_graph_search_service import CallGraphSearchService
from factories.embedding_factory import EmbeddingFactory

embedding_service = EmbeddingFactory.create_service("openai")
search_service = CallGraphSearchService(embedding_service)
```

#### Methods

##### `search_functions_with_context(query: str, limit: int = 5, max_depth: int = 3) -> List[SearchResult]`

Search functions using vector similarity with call graph context.

```python
results = search_service.search_functions_with_context(
    "authentication error handling", 
    limit=5, 
    max_depth=3
)

# Each result includes:
# - Function metadata
# - Call graph context (dependencies, dependents)
# - Call paths and graph depth
# - Enhanced relevance scoring
```

##### `build_and_store_call_graph(functions: List[FunctionMetadata]) -> Dict[str, Any]`

Build call graph and store with enhanced embeddings.

```python
stats = search_service.build_and_store_call_graph(functions)

# Returns comprehensive statistics about the stored graph
```

### HistoryManager

Track and manage analysis history.
}
```

## Analysis Approaches

The system supports two analysis approaches:

### Call Graph Approach

**Best for**: Complex codebases with intricate function relationships

```python
engine = WorkflowEngine(
    embedding_service_type="openai",
    llm_service_type="openai", 
    analysis_approach="call_graph"
)
```

**Features:**
- Analyzes function call relationships and dependencies
- Provides context-aware search with dependency trees
- Identifies root functions, leaf functions, and call paths
- Enhanced relevance scoring based on graph structure
- Stores functions with graph metadata (depth, dependency counts)

### Function Lookup Table Approach

**Best for**: Simpler codebases or when focusing on individual functions

```python
engine = WorkflowEngine(
    embedding_service_type="openai",
    llm_service_type="openai",
    analysis_approach="function_lookup_table"  # Default
)
```

**Features:**
- Direct function-to-function mapping
- Fast lookup and retrieval
- Simpler metadata storage
- Good for straightforward function analysis

## Service Factory Pattern

### EmbeddingFactory
)
```

### CallGraph

Represents the complete call graph structure.

```python
from models.call_graph_model import CallGraph, CallGraphNode

call_graph = CallGraph()

# Properties:
call_graph.nodes          # Dict[str, CallGraphNode] - All function nodes
call_graph.root_nodes     # Set[str] - Functions with no callers
call_graph.leaf_nodes     # Set[str] - Functions that call no others  
call_graph.max_depth      # int - Maximum call chain depth
```

### CallGraphNode

Represents a single function in the call graph.

```python
from models.call_graph_model import CallGraphNode

node = CallGraphNode(
    function_metadata=function,
    dependencies={"uuid-456", "uuid-789"},    # Functions this calls
    dependents={"uuid-123"},                  # Functions that call this
    depth_level=2,                           # Depth in call hierarchy
    visited=False                            # For traversal algorithms
)
```

### CallGraphSearchResult

Enhanced search result with call graph context.

```python
from models.call_graph_model import CallGraphSearchResult

result = CallGraphSearchResult(
    primary_node=node,                       # Main function found
    dependency_context=[dep1, dep2, ...],    # Related functions
    relevance_score=0.89,                    # Search relevance
    search_method="call_graph_vector_similarity",
    graph_depth=3,                           # Depth of context
    total_context_functions=8,               # Total functions in context
    call_paths=[["root", "middle", "target"]] # Paths to this function
)

# Get all functions in the result
all_functions = result.get_all_functions()

# Get context summary
summary = result.get_context_summary()
```

### SearchResult

Contains function metadata plus search relevance information. Enhanced for call graph approach.

```python
search_result = SearchResult(
    function_metadata=function,
    relevance_score=0.85,
    search_method="call_graph_vector_similarity",
    match_type="semantic_with_graph_context",
    approach_used=AnalysisApproach.CALL_GRAPH,
    nested_functions={
        'call_graph_context': {...},
        'dependency_functions': [...],
        'call_paths': [...]
    }
)
```

### AnalysisRequest

Request object for analysis operations. Supports both approaches.

```python
from models.function_model import AnalysisRequest, AnalysisApproach

request = AnalysisRequest(
    query="original user query",
    enhanced_query="AI-enhanced query",
    functions=search_results,
    context={"repo_name": "my-app"},
    approach=AnalysisApproach.CALL_GRAPH,
    call_graph_context={...}  # Additional context for call graph approach
)
```

### AnalysisResult

    print(f"System error: {e}")
```

## Configuration

### Call Graph Configuration

Configure call graph analysis behavior:

```python
# In config/settings.py
CALL_GRAPH_CONFIG = {
    "index_name": "call_graph_embeddings",
    "max_depth": 3,  # Maximum dependency traversal depth
    "settings": {...},  # OpenSearch index settings
    "mappings": {...}   # Field mappings with graph metadata
}

# Supported approaches
SUPPORTED_APPROACHES = ["function_lookup_table", "call_graph"]
DEFAULT_ANALYSIS_APPROACH = "function_lookup_table"
MAX_CALL_GRAPH_DEPTH = 3
```

### Environment Variables

```bash
# Analysis approach selection
export ANALYSIS_APPROACH="call_graph"  # or "function_lookup_table"

# OpenSearch configuration for call graph storage
export OPENSEARCH_HOST="localhost"
export OPENSEARCH_PORT="9200"
export OPENSEARCH_USER="admin"
export OPENSEARCH_PASSWORD="admin"
```

## Performance Considerations

### Call Graph Approach
- **Memory**: Higher memory usage due to graph structure storage
- **Processing**: Initial processing takes longer due to relationship analysis
- **Search**: More comprehensive results but slightly slower queries
- **Best for**: Complex applications with deep function interdependencies

### Function Lookup Table Approach  
- **Memory**: Lower memory footprint
- **Processing**: Faster initial processing
- **Search**: Quick individual function lookups
- **Best for**: Simpler applications or when analyzing isolated functions
