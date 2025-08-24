# Multi-Approach Analysis Flow

## Overview

The system supports four distinct analysis approaches that can be used individually or in combination. This flow documents how the system selects and executes different approaches based on the analysis requirements.

## 1. Approach Selection Flow

```mermaid
flowchart TD
    A[Start: User Query] --> B[Analyze Query Type]
    B --> C{Query Complexity}
    C -->|Simple Metadata| D[Function Lookup Table]
    C -->|Relationship-Based| E[Call Graph Analysis]
    C -->|Semantic Similarity| F[Vector Search]
    C -->|Complex/Unknown| G[Hybrid Approach]
    
    D --> H[Fast Metadata Search]
    E --> I[Dependency Analysis]
    F --> J[Embedding Similarity]
    G --> K[Combined Analysis]
    
    H --> L[Generate Results]
    I --> L
    J --> L
    K --> L
    
    L --> M[Confidence Assessment]
    M --> N{Confidence > Threshold?}
    N -->|Yes| O[Return Results]
    N -->|No| P[Retry with Different Approach]
    P --> B
    O --> Q[End: Analysis Complete]
```

## 2. Repository Processing Flow by Approach

```mermaid
flowchart TD
    A[Start: Process Repository] --> B[Extract Functions with AST]
    B --> C[Create Function Metadata]
    C --> D{Selected Approach}
    
    D -->|Function Lookup Table| E[Build Lookup Table]
    D -->|Call Graph| F[Build Call Graph]
    D -->|Vector Search| G[Generate Embeddings]
    D -->|Hybrid| H[Build All Structures]
    
    E --> I[Create Searchable Index]
    F --> J[Analyze Dependencies]
    G --> K[Store in OpenSearch]
    H --> L[Multi-Modal Storage]
    
    I --> M[Generate Statistics]
    J --> N[Calculate Graph Metrics]
    K --> O[Index Optimization]
    L --> P[Comprehensive Metrics]
    
    M --> Q[End: Ready for Analysis]
    N --> Q
    O --> Q
    P --> Q
```

## 3. Approach-Specific Processing

### Function Lookup Table Approach
```mermaid
flowchart LR
    A[Functions] --> B[Metadata Extraction]
    B --> C[Build Lookup Table]
    C --> D[Index by Attributes]
    D --> E[Fast Search Ready]
    
    B1[Name, Module, Class] --> C
    B2[Async, Decorators] --> C
    B3[Error Handling] --> C
    B4[Line Numbers] --> C
```

### Call Graph Approach
```mermaid
flowchart LR
    A[Functions] --> B[Extract Function Calls]
    B --> C[Build Graph Nodes]
    C --> D[Create Edges]
    D --> E[Calculate Depths]
    E --> F[Graph Ready]
    
    B1[Function Calls] --> B
    B2[Import Analysis] --> B
    B3[Builtin Filtering] --> B
```

### Vector Search Approach
```mermaid
flowchart LR
    A[Functions] --> B[Create Embeddings]
    B --> C[OpenSearch Storage]
    C --> D[k-NN Optimization]
    D --> E[Vector Search Ready]
    
    B1[Code + Metadata] --> B
    B2[OpenAI/Ollama] --> B
    B3[3072-dim Vectors] --> B
```

### Hybrid Approach
```mermaid
flowchart LR
    A[Functions] --> B[Parallel Processing]
    B --> C[Lookup Table]
    B --> D[Call Graph]
    B --> E[Vector Embeddings]
    
    C --> F[Result Fusion]
    D --> F
    E --> F
    F --> G[Hybrid Ready]
```

## 4. Query Analysis and Routing

### Query Classification
```python
def classify_query(query: str) -> AnalysisApproach:
    """Classify query to determine best approach"""
    
    # Metadata-based queries
    if has_exact_patterns(query):
        return AnalysisApproach.FUNCTION_LOOKUP_TABLE
    
    # Relationship-based queries  
    if has_dependency_keywords(query):
        return AnalysisApproach.CALL_GRAPH
    
    # Semantic queries
    if has_conceptual_terms(query):
        return AnalysisApproach.VECTOR_SEARCH
    
    # Complex/unknown queries
    return AnalysisApproach.HYBRID
```

### Approach Selection Criteria

| Query Type | Best Approach | Reasoning |
|------------|---------------|-----------|
| "Find function named 'authenticate'" | Lookup Table | Exact name matching |
| "What calls the login function?" | Call Graph | Dependency analysis |
| "Functions similar to user validation" | Vector Search | Semantic similarity |
| "Authentication issues in the system" | Hybrid | Complex, multi-faceted |

## 5. Performance Optimization Flow

```mermaid
flowchart TD
    A[Query Received] --> B[Approach Selection]
    B --> C{Cached Results?}
    C -->|Yes| D[Return Cached]
    C -->|No| E[Execute Analysis]
    
    E --> F{Results Quality}
    F -->|High| G[Cache Results]
    F -->|Low| H[Try Alternative Approach]
    
    G --> I[Return Results]
    H --> E
    D --> I
    I --> J[Update Metrics]
    J --> K[End]
```

## 6. Result Fusion for Hybrid Approach

```mermaid
flowchart TD
    A[Hybrid Analysis Request] --> B[Parallel Execution]
    B --> C[Lookup Table Results]
    B --> D[Call Graph Results]  
    B --> E[Vector Search Results]
    
    C --> F[Result Scoring]
    D --> F
    E --> F
    
    F --> G[Cross-Validation]
    G --> H[Confidence Weighting]
    H --> I[Result Ranking]
    I --> J[Top Results Selection]
    J --> K[Fused Results]
```

## 7. Error Handling and Fallbacks

### Fallback Chain
```
Primary Approach Failed → Secondary Approach → Fallback Approach → Error Response
```

### Example Fallback Scenarios
- **Call Graph Failed** → Vector Search → Lookup Table → Error
- **Vector Search Failed** → Call Graph → Lookup Table → Error  
- **Hybrid Failed** → Best Individual Approach → Simple Search → Error

## 8. Monitoring and Metrics

### Per-Approach Metrics
- **Success Rate**: Percentage of successful analyses
- **Response Time**: Average query processing time
- **Confidence Score**: Average confidence of results
- **Cache Hit Rate**: Percentage of cached responses

### Cross-Approach Comparison
- **Accuracy Validation**: Compare results across approaches
- **Performance Benchmarks**: Speed and resource usage
- **User Satisfaction**: Feedback on result quality
- **Approach Selection**: Effectiveness of automatic selection
