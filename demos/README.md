# Demo Data and Examples

This directory contains sample data files to demonstrate the Code Analysis Bot functionality with both function lookup table and call graph approaches.

## Files Overview

- **Code location information**: files, lines, modules
- **Summary statistics**: async functions, error handling coverage

### `sample_call_graph_analysis.json`
**NEW: Call Graph Analysis Examples**

Demonstrates the advanced call graph approach with 3 real-world scenarios:

1. **JWT Authentication Failures** - Call chain analysis revealing error propagation issues
2. **Database Performance Problems** - N+1 query detection through dependency analysis  
3. **Async Memory Leaks** - Resource cleanup gaps in async function chains

**Call Graph Features Demonstrated:**
- **Dependency chain analysis** with root → leaf function tracing
- **Call path visualization** showing function interaction flows
- **Graph-based problem identification** (cascading failures, resource leaks)
- **Context-aware solutions** leveraging call graph insights
- **Performance metrics** including call depth and dependency counts

### `sample_call_graph_structure.json`
**Call Graph Structure Example**

Complete call graph structure for an authentication service showing:

- **12 interconnected functions** with dependency relationships
- **Graph hierarchy**: 3 root nodes, 4 leaf nodes, max depth of 3
- **Node metadata**: depth levels, dependency/dependent counts, function roles
- **Call paths**: 4 different execution flows through the graph
- **Analysis examples**: dependency analysis and call path insights

**Graph Types Demonstrated:**
- **Root nodes**: Entry points (login_handler, etc.)
- **Intermediate nodes**: Processing functions with both callers and callees
- **Leaf nodes**: Terminal functions (database operations, utilities)

## Using Demo Data

### 1. Import Analysis History
2. **Run several analyses** to build history
3. **Export data** using the built-in export functions
4. **Use as examples** for documentation and testing

## Call Graph Approach Usage Examples

### 1. Initialize with Call Graph Approach
```python
from core.workflow_engine import WorkflowEngine

# Initialize with call graph analysis
engine = WorkflowEngine(
    embedding_service_type="openai",
    llm_service_type="openai", 
    analysis_approach="call_graph"
)

# Process repository with call graph building
result = engine.process_repository("/path/to/repo")
print(f"Graph statistics: {result['graph_statistics']}")
```

### 2. Analyze Issues with Call Graph Context
```python
# Query with call graph-enhanced analysis
analysis = engine.analyze_user_issue(
    "JWT validation is failing", 
    context={"priority": "high"}
)
