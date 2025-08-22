# API Documentation

Programmatic API for the Code Analysis Bot system.

## Core Classes

### WorkflowEngine

Main orchestrator for repository processing and issue analysis.

```python
from core.workflow_engine import WorkflowEngine

engine = WorkflowEngine(
    embedding_service_type="openai",  # "openai", "ollama", "perplexity"
    llm_service_type="openai"         # "openai", "perplexity", "ollama"
)
```

#### Methods

##### `process_repository(repo_path: str) -> Dict[str, Any]`

Process a repository and create function embeddings.

```python
result = engine.process_repository("/path/to/repository")

# Returns:
{
    "total_functions": 150,
    "embedded_functions": 148,
    "summary": {
        "async_functions": 25,
        "functions_with_error_handling": 67,
        "unique_modules": 12
    }
}
```

##### `analyze_user_issue(query: str, context: Dict = None) -> Dict[str, Any]`

Analyze a user-reported issue with AI.

```python
result = engine.analyze_user_issue(
    "Authentication function throwing JWT errors",
    context={"repo_name": "my-app", "tech_stack": ["python", "flask"]}
)

# Returns:
{
    "query": "Authentication function throwing JWT errors",
    "enhanced_query": "Authentication function JWT token validation errors...",
    "functions_found": 5,
    "analysis": "Detailed technical analysis...",
    "confidence_score": 0.85,
    "functions_analyzed": 5,
    "search_results": [...]
}
```

### FunctionLookupTable

Manage function metadata and relationships.

```python
from core.function_lookup import FunctionLookupTable

lookup = FunctionLookupTable()
lookup.build_lookup_table(functions)
```

#### Methods

##### `get_most_relevant_functions(query: str, limit: int = 5) -> List[FunctionMetadata]`

Find most relevant functions for a query.

```python
functions = lookup.get_most_relevant_functions("authentication", limit=5)
```

##### `export_to_json(filepath: str)`

Export function lookup table to JSON.

```python
lookup.export_to_json("function_lookup.json")
```

##### `get_nested_functions(lookup_id: str) -> List[FunctionMetadata]`

Get all nested functions called by a function.

```python
nested = lookup.get_nested_functions("func-uuid-123")
```

### HistoryManager

Track and manage analysis history.

```python
from utils.history_manager import HistoryManager

history = HistoryManager("custom_history.json")
```

#### Methods

##### `add_analysis(...)`

Add a new analysis to history.

```python
history.add_analysis(
    query="User login failing",
    enhanced_query="User authentication login validation errors...",
    analysis_result="The issue is in the JWT validation...",
    confidence_score=0.9,
    functions_analyzed=3,
    embedding_service="openai",
    llm_service="openai",
    context={"repo": "webapp"}
)
```

##### `get_statistics() -> Dict[str, Any]`

Get analysis statistics.

```python
stats = history.get_statistics()

# Returns:
{
    "total_analyses": 45,
    "average_confidence": 0.82,
    "services_usage": {"openai+openai": 30, "ollama+ollama": 15},
    "created_at": "2024-01-15T10:30:00",
    "last_updated": "2024-01-15T15:45:00"
}
```

## Service Factory Pattern

### EmbeddingFactory

```python
from factories.embedding_factory import EmbeddingFactory

# Create embedding service
embedder = EmbeddingFactory.create_service("openai")
embedding = embedder.create_query_embedding("search query")
```

### LLMFactory

```python
from factories.llm_factory import LLMFactory

# Create analysis service
analyzer = LLMFactory.create_analysis_service("openai")

# Create query enhancer
enhancer = LLMFactory.create_query_enhancer("perplexity")
```

## Data Models

### FunctionMetadata

```python
from models.function_model import FunctionMetadata

function = FunctionMetadata(
    name="authenticate_user",
    lookup_id="uuid-123",
    file_path="/src/auth.py",
    repository_name="webapp",
    module_name="src.auth",
    nested_call_ids=["uuid-456", "uuid-789"],
    start_line=25,
    end_line=45,
    code="def authenticate_user(token):\n    ...",
    is_async=False,
    class_context="AuthManager",
    calls=["validate_token", "get_user"],
    imports=["jwt", "hashlib"],
    decorators=["@require_auth"],
    error_handling={"has_try_catch": True},
    line_numbers=[25, 26, 27, ...]
)
```

### SearchResult

Contains function metadata plus search relevance information.

### AnalysisRequest

Request object for analysis operations.

### AnalysisResult

Result object with analysis, confidence score, and additional context needs.

## Error Handling

All services include proper error handling and return appropriate error messages or None values when operations fail.

```python
try:
    result = engine.analyze_user_issue("query")
    if "error" in result:
        print(f"Analysis failed: {result['error']}")
    else:
        print(f"Analysis: {result['analysis']}")
except Exception as e:
    print(f"System error: {e}")
```
+