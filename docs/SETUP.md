# Setup Guide

Complete setup guide for the Code Analysis Bot system.

## Prerequisites

- Python 3.8 or higher
- OpenSearch 2.3.0 or higher
- Git
- One or more API keys:
  - OpenAI API key (recommended)
  - Perplexity API key (optional)
  - Ollama installed locally (optional)

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/on_call_bot.git
cd on_call_bot
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements_updated.txt
```

### 4. Setup Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
nano .env
```

Add your API keys to `.env`:

```env
# Required for OpenAI services
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: For Perplexity services  
PERPLEXITY_API_KEY=your-perplexity-api-key-here

# Optional: For Ollama (if not using localhost:11434)
OLLAMA_BASE_URL=http://localhost:11434
```

### 5. Setup OpenSearch

#### Option A: Docker (Recommended)

```bash
# Start OpenSearch container
docker run -d \
  --name opensearch \
  -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "plugins.security.disabled=true" \
  -e "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" \
  opensearchproject/opensearch:2.3.0

# Verify OpenSearch is running
curl http://localhost:9200
```

#### Option B: Local Installation

1. Download OpenSearch from [opensearch.org](https://opensearch.org/)
2. Extract and configure
3. Start OpenSearch service

### 6. Setup Ollama (Optional)

If you want to use Ollama for local LLM processing:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull codellama:7b
ollama pull nomic-embed-text

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

## Verification

### Test Installation

```bash
# Test the system
python main_structured.py
```

### Test Streamlit UI

```bash
# Launch web interface
streamlit run ui/streamlit_app.py
```

## Troubleshooting

### Common Issues

#### OpenSearch Connection Error
```
Error: Connection refused to localhost:9200
```

**Solution:**
- Ensure OpenSearch is running: `docker ps` or check service status
- Check port 9200 is not blocked by firewall
- Verify OpenSearch configuration in `config/settings.py`

#### API Key Errors
```
Error: Invalid API key
```

**Solution:**
- Verify API keys in `.env` file
- Ensure no extra spaces or quotes around keys
- Check API key permissions and quotas

#### Memory Issues
```
Error: Out of memory
```

**Solution:**
- Increase OpenSearch heap size: `-e "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g"`
- Process smaller repositories
- Use pagination for large datasets

#### Python Import Errors
```
ModuleNotFoundError: No module named 'xyz'
```

**Solution:**
- Ensure virtual environment is activated
- Reinstall requirements: `pip install -r requirements_updated.txt`
- Check Python version compatibility

## Performance Optimization

### For Large Repositories
- Use OpenAI embeddings for better performance
- Increase OpenSearch memory allocation
- Process repositories in smaller chunks

### For Better Analysis
- Use GPT-4 for higher quality analysis
- Combine multiple LLM providers for comparison
- Tune confidence thresholds based on your needs

## Next Steps

1. Process your first repository
2. Try different LLM combinations
3. Export function lookup tables
4. Explore analysis history
5. Customize confidence thresholds

For more advanced configuration, see [CONFIGURATION.md](CONFIGURATION.md).
+