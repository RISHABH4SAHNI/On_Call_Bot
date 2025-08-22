import os
from typing import Dict, Any

OPENSEARCH_CONFIG = {
    "hosts": [{"host": "localhost", "port": 9200}],
    "http_auth": ("admin", "admin"),
    "use_ssl": False
}

OPENAI_CONFIG = {
    "model": "text-embedding-3-large",
    "embedding_dimensions": 3072,
    "chat_model": "gpt-4"
}

PERPLEXITY_CONFIG = {
    "embedding_model": "text-embedding-3-large",
    "chat_model": "llama-3.1-8b-instruct",
    "embedding_dimensions": 3072,
    "base_url": "https://api.perplexity.ai"
}

OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "embedding_model": "nomic-embed-text",
    "chat_model": "codellama:7b",
    "embedding_dimensions": 768
}

INDEX_CONFIG = {
    "name": "code_embeddings",
    "settings": {"index": {"knn": True}},
    "mappings": {
        "properties": {
            "embedding": {"type": "dense_vector", "dims": 3072},
            "embedding_knn": {"type": "knn_vector", "dimension": 3072},
            "func_name": {"type": "keyword"},
            "lookup_id": {"type": "keyword"},
            "file_path": {"type": "keyword"},
            "repository_name": {"type": "keyword"},
            "module_name": {"type": "keyword"},
            "code": {"type": "text"},
            "calls": {"type": "keyword"},
            "is_async": {"type": "boolean"},
            "start_line": {"type": "integer"},
            "end_line": {"type": "integer"},
            "class_context": {"type": "keyword"},
            "nested_call_ids": {"type": "keyword"},
            "decorators": {"type": "keyword"},
            "error_handling": {"type": "object"}
        }
    }
}

CONFIDENCE_THRESHOLD = 0.8
MAX_ANALYSIS_ITERATIONS = 3
DEFAULT_FUNCTION_LIMIT = 5
