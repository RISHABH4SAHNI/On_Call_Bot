# Code Analysis Bot - Restructured

A clean, modular AI-powered code analysis system that processes repositories, creates function embeddings, and provides intelligent issue analysis with confidence scoring.

## Features

- **Repository Processing**: Extract and analyze Python functions from codebases
- **Function Lookup Table**: Comprehensive function metadata with nested call relationships
- **Multi-LLM Support**: OpenAI GPT, Perplexity, and Ollama integration
- **Multi-Embedding Support**: OpenAI, Ollama, and Perplexity embeddings
- **Vector Search**: Semantic search using OpenSearch with k-NN
- **Confidence Scoring**: Interactive analysis with 0.8 confidence threshold
- **Streamlit UI**: Modern web interface for easy interaction
- **Clean Architecture**: Factory pattern with modular, testable code

## Architecture

```
on_call_bot/
├── models/              # Data models and schemas
├── core/               # Core business logic
├── services/           # Service layer (embeddings, search, analysis)
├── factories/          # Factory pattern implementations
├── ui/                # Streamlit user interface
├── config/            # Configuration and settings
├── utils/             # Utility functions
└── main_structured.py # Clean entry point
```

## Installation

1. **Clone and setup**:
```bash
git clone <repository>
cd on_call_bot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements_updated.txt
```

3. **Setup environment**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Setup OpenSearch** (required):
```bash
# Using Docker
docker run -d \
  --name opensearch \
  -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "plugins.security.disabled=true" \
  opensearchproject/opensearch:2.3.0
```

## Configuration

Create `.env` file with your API keys:

```env
# Required for OpenAI services
OPENAI_API_KEY=your_openai_api_key

# Optional: For Perplexity services
PERPLEXITY_API_KEY=your_perplexity_api_key

# Optional: For Ollama (if not using localhost:11434)
OLLAMA_BASE_URL=http://localhost:11434
```

## Usage

### Command Line Interface

```bash
python main_structured.py
```

**Options:**
1. **Process Repository** - Extract functions and create embeddings
2. **Analyze Issue** - AI-powered issue analysis with confidence scoring
3. **Launch Streamlit UI** - Web interface
4. **Export Function Lookup Table** - Export to CSV
5. **Exit**

### Streamlit Web UI

```bash
streamlit run ui/streamlit_app.py
```

Access at: http://localhost:8501

### Programmatic Usage

```python
from core.workflow_engine import WorkflowEngine

# Initialize workflow engine
engine = WorkflowEngine(
    embedding_service_type="openai",  # or "ollama", "perplexity"
    llm_service_type="openai"         # or "perplexity", "ollama"
)

# Process repository
result = engine.process_repository("/path/to/repo")

# Analyze issue
analysis = engine.analyze_user_issue(
    "Authentication function throwing JWT errors",
    context={"repo_name": "my-app"}
)
```

## Workflow

1. **Repository Processing**:
   - Parse Python files using AST
   - Extract function metadata (calls, decorators, error handling)
   - Create embeddings using chosen service
   - Store in OpenSearch with k-NN indexing
   - Build function lookup table with nested relationships

2. **Issue Analysis**:
   - Enhance user query with technical context
   - Vector search for relevant functions (top 5)
   - Include nested function calls in analysis
   - Interactive confidence-based analysis (threshold: 0.8)
   - Request additional context if confidence < 0.8
   - Provide detailed technical analysis with suggested fixes

## Key Components

- **FunctionMetadata**: Complete function information with lookup IDs
- **WorkflowEngine**: Orchestrates the entire analysis pipeline
- **ServiceFactory**: Clean factory pattern for all services
- **VectorSearchService**: Semantic search with OpenSearch k-NN
- **AnalysisService**: Confidence-based iterative analysis
- **QueryEnhancementService**: Technical context enhancement

## API Support

- **OpenAI**: GPT-4 for analysis, text-embedding-3-large for embeddings
- **Perplexity**: Llama-3.1-8b-instruct for analysis and embeddings
- **Ollama**: Local CodeLlama:7b and nomic-embed-text

## License

MIT License
