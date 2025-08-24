# Setup Guide

Complete setup guide for the Code Analysis Bot system with support for Call Graph Analysis, Function Lookup Tables, and Vector Search approaches.

## Prerequisites

curl http://localhost:9200
```

**Note on OpenSearch Requirements:**
- **Call Graph Analysis**: OpenSearch optional (can work without vector search)
- **Function Lookup Table**: OpenSearch not required (uses in-memory tables)
- **Vector Search**: OpenSearch required for embedding storage
- **Hybrid Approach**: OpenSearch recommended for full functionality

### Quick Setup for Different Approaches

```bash
# Minimal setup for Function Lookup Table approach only
# (No OpenSearch required)
pip install -r requirements.txt
cp .env.example .env
# Add only: OPENAI_API_KEY=your_key

# Full setup for all approaches including Vector Search
# (OpenSearch required)
docker run -d --name opensearch -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "plugins.security.disabled=true" \
  opensearchproject/opensearch:2.3.0

# Verify setup
python main_structured.py  # Choose option 8 for System Diagnostics
```

#### Option B: Local Installation

1. Download OpenSearch from [opensearch.org](https://opensearch.org/)

## Verification

### Test Different Analysis Approaches

#### 1. Test Function Lookup Table (Fastest Setup)

```bash
# Test the system with lookup table approach
python main_structured.py
# Choose option 1 (Process Repository)
# Select approach: lookup_table
# Embedding service: openai
# LLM service: openai
```

This approach:
- ✅ Works without OpenSearch
- ⚡ Fast processing and search
- 📊 Rich metadata analysis
- 💾 Low memory usage

#### 2. Test Call Graph Analysis

```bash
python main_structured.py
# Choose option 1 (Process Repository) 
# Select approach: call_graph
# Embedding service: openai
# LLM service: openai
```

This approach:
- 🕸️ Builds function relationship graph
- 🔍 Analyzes dependencies and call paths
- 📈 Higher memory usage but powerful insights
- ⚙️ Can work with or without OpenSearch

#### 3. Test Full Vector Search

```bash
# Ensure OpenSearch is running first
curl http://localhost:9200

python main_structured.py
# Choose option 1 (Process Repository)
# Select approach: vector_search  
# Embedding service: openai
# LLM service: openai
```

This approach:
- 🧠 Semantic similarity search
- 🔍 Embedding-based matching
- 📡 Requires OpenSearch for vector storage

### Test Installation

```bash
- Check Python version compatibility

## Performance Optimization

### Approach-Specific Optimization

#### Function Lookup Table Optimization
```bash
# For large repositories (>10,000 functions)
export LOOKUP_TABLE_BATCH_SIZE=1000
export ENABLE_LOOKUP_INDEXING=true
export EXPORT_FORMAT_COMPRESSION=true
```

Benefits:
- Minimal memory footprint
- Fast search operations
- Efficient for metadata-heavy analysis

#### Call Graph Optimization
```bash
# For complex repositories with deep call chains
export MAX_CALL_GRAPH_DEPTH=5
export ENABLE_GRAPH_CACHING=true
export PRUNE_EXTERNAL_CALLS=true
```

Settings explanation:
- `MAX_CALL_GRAPH_DEPTH`: Limits traversal depth (default: 10)
- `ENABLE_GRAPH_CACHING`: Caches graph structures
- `PRUNE_EXTERNAL_CALLS`: Excludes library calls

#### Vector Search Optimization
```bash
# For better embedding performance
export OPENSEARCH_BULK_SIZE=500
export EMBEDDING_BATCH_SIZE=100
export VECTOR_DIMENSION=1536  # for OpenAI embeddings
```

### For Large Repositories

**Repository Size Guidelines:**

| Repository Size | Recommended Approach | Setup Notes |
|----------------|---------------------|-------------|
| < 1,000 functions | Any approach | All work well |
| 1,000 - 5,000 functions | Lookup Table or Call Graph | Vector search slower |
| 5,000 - 10,000 functions | Lookup Table recommended | Call graph needs tuning |
| > 10,000 functions | Lookup Table + selective Call Graph | Hybrid with depth limits |

**Optimization strategies:**
- Use Function Lookup Table for initial exploration
- Use Call Graph for specific dependency analysis
- Use Vector Search for semantic similarity when needed
- Increase OpenSearch memory allocation
- Process repositories in smaller chunks

### Memory Usage by Approach

```bash
# Monitor memory usage during processing
# Function Lookup Table: ~50MB per 1000 functions
# Call Graph: ~200MB per 1000 functions  
# Vector Search: ~150MB per 1000 functions
# Hybrid: ~350MB per 1000 functions
```

### For Better Analysis

**Approach Selection Strategy:**
```bash
# Start with Function Lookup Table for fast overview
python main_structured.py  # approach: lookup_table

# Switch to Call Graph for dependency analysis  
python main_structured.py  # approach: call_graph

# Use Vector Search for semantic similarity
python main_structured.py  # approach: vector_search

# Use Hybrid for comprehensive analysis
python main_structured.py  # approach: hybrid
```

- Use GPT-4 for higher quality analysis
- Combine multiple LLM providers for comparison
- Tune confidence thresholds based on your needs

## Next Steps

1. Process your first repository
2. **Experiment with approaches:**
   - Start with Function Lookup Table (fastest)
   - Try Call Graph Analysis (relationships)
   - Test Vector Search (semantic similarity)
   - Compare results with Hybrid approach
3. **Try different LLM combinations:**
   - OpenAI for production quality
   - Perplexity for balanced performance  
   - Ollama for local/offline processing
4. **Export and analyze data:**
   - Export function lookup tables (CSV/JSON)
   - Export analysis history
   - Generate function relationship reports
5. **Customize for your needs:**
   - Tune confidence thresholds
   - Adjust call graph depth limits
   - Configure approach-specific parameters

## Approach-Specific Configuration

### Function Lookup Table Configuration

```bash
# In .env file
LOOKUP_TABLE_EXPORT_FORMAT=json  # json, csv, or both
LOOKUP_INCLUDE_CODE_SNIPPETS=false  # Include function code
LOOKUP_MAX_RESULTS_PER_QUERY=20
LOOKUP_ENABLE_FUZZY_MATCHING=true
```

### Call Graph Configuration

```bash
# In .env file
CALL_GRAPH_MAX_DEPTH=10
CALL_GRAPH_INCLUDE_EXTERNAL=false
CALL_GRAPH_DETECT_CYCLES=true
CALL_GRAPH_PRUNE_LEAVES=false
CALL_GRAPH_CACHE_RESULTS=true
```

### Vector Search Configuration

```bash
# In .env file
OPENSEARCH_HOST=localhost:9200
OPENSEARCH_INDEX_NAME=code_analysis
VECTOR_DIMENSION=1536
VECTOR_SIMILARITY_THRESHOLD=0.7
ENABLE_HYBRID_SEARCH=true
```

## Development Setup

### For Contributing to Different Approaches

```bash
# Clone repository
git clone https://github.com/yourusername/on_call_bot.git
cd on_call_bot

# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Additional dev dependencies

# Test individual approaches
pytest tests/test_function_lookup.py     # Lookup table tests
pytest tests/test_call_graph_processor.py  # Call graph tests
pytest tests/test_vector_search.py       # Vector search tests
pytest tests/test_workflow_engine.py     # Integration tests

# Run system diagnostics
python main_structured.py  # Option 8: System Diagnostics
```

For more advanced configuration, see [CONFIGURATION.md](CONFIGURATION.md).
