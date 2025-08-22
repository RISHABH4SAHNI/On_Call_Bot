# Demo Data and Examples

This directory contains sample data files to demonstrate the Code Analysis Bot functionality.

## Files Overview

### `sample_analysis_history.json`
Complete example of analysis history with 5 different code issue analyses:

1. **JWT Authentication Issues** - Token validation problems
2. **Database Timeout Issues** - Bulk insert performance problems  
3. **Memory Leak** - Async task management issues
4. **API Performance** - Response time optimization
5. **File Upload Issues** - Large file handling problems

**Features demonstrated:**
- Different confidence scores (0.78 - 0.94)
- Multiple LLM services (OpenAI, Perplexity, Ollama)
- Various tech stacks and priorities
- Detailed analysis with actionable solutions

### `sample_function_lookup.json`
Example function lookup table export showing:

- **4 interconnected functions** from a web application
- **Nested function relationships** with lookup IDs
- **Function metadata**: decorators, error handling, async status
- **Code location information**: files, lines, modules
- **Summary statistics**: async functions, error handling coverage

## Using Demo Data

### 1. Import Analysis History
```python
from utils.history_manager import HistoryManager

history = HistoryManager("sample_history.json")
stats = history.get_statistics()
recent = history.get_recent_analyses(3)
```

### 2. Load Function Lookup Data
```python
import json

with open('demos/sample_function_lookup.json', 'r') as f:
    lookup_data = json.load(f)
    print(f"Total functions: {lookup_data['summary']['total_functions']}")
```

### 3. View in Streamlit UI
- Start the Streamlit app: `streamlit run ui/streamlit_app.py`
- The history sidebar will show analysis statistics
- Function lookup export will generate similar JSON files

## Creating Your Own Demo Data

1. **Process a real repository** to generate actual function data
2. **Run several analyses** to build history
3. **Export data** using the built-in export functions
4. **Use as examples** for documentation and testing
+