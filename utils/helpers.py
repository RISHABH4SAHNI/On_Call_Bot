import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

def validate_repository_path(repo_path: str) -> bool:
    """Validate if the given path is a valid repository"""
    if not repo_path or not os.path.exists(repo_path):
        return False
    
    path = Path(repo_path)
    return path.is_dir() and any(path.rglob("*.py"))

def get_python_files(repo_path: str, exclude_patterns: List[str] = None) -> List[str]:
    """Get all Python files from repository excluding test files and common excludes"""
    if exclude_patterns is None:
        exclude_patterns = [
            r'test_.*\.py$',
            r'.*_test\.py$',
            r'.*/tests/.*',
            r'.*/test/.*',
            r'.*/__pycache__/.*',
            r'.*/\.git/.*',
            r'.*/venv/.*',
            r'.*/env/.*'
        ]
    
    python_files = []
    for root, dirs, files in os.walk(repo_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not any(re.match(pattern, os.path.join(root, d)) for pattern in exclude_patterns)]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                # Check if file matches any exclude pattern
                if not any(re.match(pattern, file_path) for pattern in exclude_patterns):
                    python_files.append(file_path)
    
    return python_files

def extract_repo_name(repo_path: str) -> str:
    """Extract repository name from path"""
    return Path(repo_path).name

def calculate_confidence_score(analysis_text: str) -> float:
    """Calculate confidence score based on analysis text patterns"""
    confidence_indicators = {
        'high': ['definitely', 'clearly', 'obvious', 'certain', 'exactly', 'precisely'],
        'medium': ['likely', 'probably', 'appears', 'seems', 'suggests', 'indicates'],
        'low': ['might', 'could', 'possibly', 'maybe', 'uncertain', 'unclear']
    }
    
    text_lower = analysis_text.lower()
    
    high_count = sum(1 for word in confidence_indicators['high'] if word in text_lower)
    medium_count = sum(1 for word in confidence_indicators['medium'] if word in text_lower)
    low_count = sum(1 for word in confidence_indicators['low'] if word in text_lower)
    
    total_indicators = high_count + medium_count + low_count
    
    if total_indicators == 0:
        return 0.5
    
    confidence = (high_count * 1.0 + medium_count * 0.6 + low_count * 0.2) / total_indicators
    return min(max(confidence, 0.0), 1.0)

def format_code_snippet(code: str, max_lines: int = 20) -> str:
    """Format code snippet for display"""
    lines = code.split('\n')
    if len(lines) <= max_lines:
        return code
    
    return '\n'.join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"

def extract_function_signature(code: str) -> str:
    """Extract function signature from code"""
    lines = code.split('\n')
    for line in lines:
        if line.strip().startswith(('def ', 'async def ')):
            return line.strip()
    return ""

def clean_error_message(error_msg: str) -> str:
    """Clean and format error messages"""
    return re.sub(r'\s+', ' ', error_msg.strip())

def get_file_extension(file_path: str) -> str:
    """Get file extension"""
    return Path(file_path).suffix

def is_test_file(file_path: str) -> bool:
    """Check if file is a test file"""
    file_name = Path(file_path).name.lower()
    return (file_name.startswith('test_') or 
            file_name.endswith('_test.py') or 
            'test' in Path(file_path).parts)
