# Repository Processing and Analysis Flow

## Overview

This document describes the comprehensive flow for repository processing and user issue analysis, supporting multiple analysis approaches including Call Graph Analysis, Function Lookup Tables, Vector Search, and Hybrid approaches.

## 1. Repository Processing Flow (Multi-Approach)

```mermaid
flowchart TD
    A[Start: Process Repository] --> B[Extract Repo Info from URL]
    B --> C[Select Analysis Approach]
    C --> D[Read Dependencies & Config]
    D --> E[List All Files in Repository]
    E --> F{File is Python?}
    F -->|No| G[Skip File]
    F -->|Yes| H{Is Test File?}
    H -->|Yes| I[Skip Test File]
    H -->|No| J[Parse Functions using AST]
    J --> K[Extract Function Metadata]
    K --> L{Analysis Approach}
    
    L -->|Function Lookup Table| M[Build Lookup Table]
    L -->|Call Graph| N[Build Call Graph]
    L -->|Vector Search| O[Generate Embeddings]
    L -->|Hybrid| P[Execute All Approaches]
    
    M --> Q[Create Searchable Index]
    N --> R[Analyze Dependencies & Store]
    O --> S[Create & Upload Embeddings]
    P --> T[Multi-Modal Processing]
    
    Q --> U[Generate Summary Statistics]
    R --> V[Generate Graph Statistics]
    S --> W[Generate Embedding Statistics]
    T --> X[Generate Comprehensive Statistics]
    
    U --> Y[End: Repository Processed]
    V --> Y
    W --> Y
    X --> Y
    
    G --> E
    I --> E
```

## 2. Function Metadata Extraction (Enhanced)

```mermaid
flowchart TD
    A[Python File] --> B[AST Parsing]
    B --> C[Extract Functions]
    C --> D[For Each Function]
    D --> E[Basic Metadata]
    E --> F[Call Analysis]
    F --> G[Import Analysis]
    G --> H[Decorator Analysis]
    H --> I[Error Handling Analysis]
    I --> J[Create Function Metadata]
    J --> K{More Functions?}
    K -->|Yes| D
    K -->|No| L[Function List Complete]
    
    E1[Name, Line Numbers] --> E
    E2[Class Context] --> E
    E3[Async Status] --> E
    
    F1[Function Calls] --> F
    F2[Method Calls] --> F
    
    G1[Project Imports] --> G
    G2[Standard Library] --> G
    
    H1[Decorator List] --> H
    H2[Decorator Args] --> H
    
    I1[Try-Catch Blocks] --> I
    I2[Exception Types] --> I
```

## 3. Call Graph Construction Process

```mermaid
flowchart TD
    A[Function Metadata List] --> B[Initialize Call Graph]
    B --> C[Add All Functions as Nodes]
    C --> D[Build Function Name Mapping]
    D --> E[For Each Function]
    E --> F[Analyze Function Calls]
    F --> G[Filter Builtin Functions]
    G --> H[Create Call Edges]
    H --> I{More Functions?}
    I -->|Yes| E
    I -->|No| J[Identify Root Nodes]
    J --> K[Identify Leaf Nodes]
    K --> L[Calculate Node Depths]
    L --> M[Generate Graph Statistics]
    M --> N[Call Graph Complete]
```

## 4. Enhanced Embedding Generation

```mermaid
flowchart TD
    A[Function Metadata] --> B{Approach Type}
    B -->|Vector Search| C[Standard Embedding]
    B -->|Call Graph| D[Graph-Enhanced Embedding]
    B -->|Hybrid| E[Multi-Context Embedding]
    
    C --> F[Function Code + Metadata]
    D --> G[Function + Graph Context]
    E --> H[Function + Graph + Lookup Context]
    
    F --> I[Generate Embedding]
    G --> I
    H --> I
    
    I --> J{Embedding Success?}
    J -->|No| K[Log Error & Continue]
    J -->|Yes| L[Store in OpenSearch]
    L --> M{Storage Success?}
    M -->|No| N[Log Storage Error]
    M -->|Yes| O[Update Counter]
    
    K --> P{More Functions?}
    N --> P
    O --> P
    P -->|Yes| A
    P -->|No| Q[Embedding Process Complete]
```

## 5. Multi-Approach User Issue Analysis

```mermaid
flowchart TD
    A[User Input: Issue/Query] --> B[Context Collection]
    B --> C[Auto-detect Environment]
    C --> D[Auto-detect Git Context]
    D --> E[Query Enhancement with LLM]
    E --> F[Approach Selection/Configuration]
    F --> G{Selected Approach}
    
    G -->|Function Lookup Table| H[Metadata Search]
    G -->|Call Graph| I[Graph-Based Search]
    G -->|Vector Search| J[Embedding Similarity]
    G -->|Hybrid| K[Multi-Modal Search]
    
    H --> L[Fast Lookup Results]
    I --> M[Dependency Context Results]
    J --> N[Semantic Similarity Results]
    K --> O[Fused Results]
    
    L --> P[Confidence Assessment]
    M --> P
    N --> P
    O --> P
    
    P --> Q{Confidence > Threshold?}
    Q -->|No| R[Iterative Refinement]
    Q -->|Yes| S[Context Integration]
    
    R --> T[Enhanced Search Strategy]
    T --> G
    
    S --> U[LLM Analysis with Context]
    U --> V[Generate Technical Analysis]
    V --> W[History Tracking]
    W --> X[Return Analysis Results]
    X --> Y[End: Analysis Complete]
```

## 6. Detailed Process Steps by Approach

### Function Lookup Table Approach:
1. **Index Creation**
   - Build searchable metadata index
   - Support filtering by multiple attributes
   - Create export capabilities (CSV/JSON)

2. **Fast Search**
   - Direct metadata matching
   - Pattern-based filtering
   - Instant results for exact matches

### Call Graph Approach:
1. **Graph Construction**
   - Build complete dependency graph
   - Calculate node depths and relationships
   - Identify critical paths and components

2. **Context-Aware Search**
   - Include dependency context in results
   - Provide call path analysis
   - Enable impact assessment

### Vector Search Approach:
1. **Embedding Generation**
   - Create semantic embeddings
   - Store in optimized OpenSearch index
   - Support k-NN similarity search

2. **Semantic Search**
   - Find conceptually similar functions
   - Cross-language pattern recognition
   - Context-aware similarity scoring

### Hybrid Approach:
1. **Parallel Execution**
   - Run multiple approaches simultaneously
   - Cross-validate results
   - Combine strengths of each method

2. **Result Fusion**
   - Intelligent result merging
   - Confidence-based weighting
   - Comprehensive analysis coverage

## 7. Enhanced Context Collection

### Automatic Context Detection:
```
Environment Context:
- OS, Python version, available memory
- Git branch, recent commits, repository info
- Error logs, performance metrics
- Technology stack, dependencies

Analysis Context:
- Query complexity assessment
- Historical similar queries
- Approach effectiveness patterns
- User preferences and feedback
```

## 8. Confidence Scoring and Quality Assessment

### Multi-Dimensional Confidence:
- **Search Relevance**: How well results match query
- **Context Completeness**: Adequacy of context information
- **Cross-Approach Agreement**: Consistency across methods
- **Historical Performance**: Success rate for similar queries

### Quality Metrics:
- **Coverage**: Percentage of relevant functions found
- **Precision**: Accuracy of returned results
- **Completeness**: Depth of analysis provided
- **Actionability**: Usefulness of recommendations

## 9. Advanced Error Handling

### Service-Level Errors:
- **LLM Service Failures**: Automatic fallback to alternative services
- **OpenSearch Unavailable**: Graceful degradation to in-memory search
- **Embedding Generation Errors**: Continue with available functions
- **Graph Construction Issues**: Partial graph with warnings

### Analysis-Level Errors:
- **Low Confidence Results**: Automatic refinement strategies
- **No Results Found**: Expanded search scope and alternative approaches
- **Context Overload**: Intelligent context truncation and prioritization
- **Inconsistent Results**: Cross-validation and conflict resolution

## 10. Performance Optimization Strategies

### Caching Layers:
- **Query Result Caching**: Cache frequent query results
- **Embedding Caching**: Reuse generated embeddings
- **Graph Structure Caching**: Persist call graph between sessions
- **Context Caching**: Store processed context information

### Parallel Processing:
- **Multi-Approach Execution**: Run approaches in parallel
- **Batch Processing**: Process multiple functions simultaneously
- **Async Operations**: Non-blocking I/O for external services
- **Resource Pooling**: Efficient resource utilization

## 11. Monitoring and Analytics

### Real-Time Metrics:
- **Processing Speed**: Repository analysis time
- **Search Latency**: Query response time
- **Success Rates**: Analysis effectiveness
- **Resource Usage**: Memory and CPU utilization

### Historical Analytics:
- **Approach Effectiveness**: Success rates by approach
- **Query Patterns**: Common query types and trends
- **User Satisfaction**: Feedback and usage patterns
- **System Performance**: Long-term performance trends
