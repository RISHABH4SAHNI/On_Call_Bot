import os
import ast
import uuid
from pathlib import Path
from typing import List, Dict, Any
from models.function_model import FunctionMetadata

class RepositoryProcessor:
    def __init__(self):
        self.function_lookup = {}
        self.builtin_functions = {
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray', 'bytes',
            'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir',
            'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float', 'format', 'frozenset',
            'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int',
            'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
            'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'print',
            'property', 'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice',
            'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'
        }

    def process_repository(self, repo_path: str) -> List[FunctionMetadata]:
        functions = []
        python_files = self._get_python_files(repo_path)
        
        for file_path in python_files:
            file_functions = self._process_file(file_path, repo_path)
            functions.extend(file_functions)
        
        self._build_nested_call_relationships(functions)
        return functions

    def _get_python_files(self, repo_path: str) -> List[str]:
        python_files = []
        excluded_dirs = {'tests', 'test', '.git', 'venv', '__pycache__', '.pytest_cache'}
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    python_files.append(os.path.join(root, file))
        
        return python_files

    def _process_file(self, file_path: str, repo_path: str) -> List[FunctionMetadata]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            extractor = FunctionExtractor(file_path, repo_path, source_code)
            return extractor.extract_functions(tree)
        except Exception:
            return []

    def _build_nested_call_relationships(self, functions: List[FunctionMetadata]):
        for func in functions:
            nested_ids = []
            for call in func.calls:
                if call not in self.builtin_functions:
                    for other_func in functions:
                        if other_func.name == call and other_func.lookup_id != func.lookup_id:
                            nested_ids.append(other_func.lookup_id)
            func.nested_call_ids = nested_ids

class FunctionExtractor:
    def __init__(self, file_path: str, repo_path: str, source_code: str):
        self.file_path = file_path
        self.repo_path = repo_path
        self.source_code = source_code
        self.imports = []
        self.current_class = None

    def extract_functions(self, tree: ast.AST) -> List[FunctionMetadata]:
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    self.imports.append(f"{module}.{alias.name}" if module else alias.name)
            elif isinstance(node, ast.ClassDef):
                self.current_class = node.name
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_metadata = self._extract_function_metadata(node)
                if func_metadata:
                    functions.append(func_metadata)
        return functions

    def _extract_function_metadata(self, node: ast.FunctionDef) -> FunctionMetadata:
        lookup_id = str(uuid.uuid4())
        repo_name = Path(self.repo_path).name
        module_name = os.path.relpath(self.file_path, self.repo_path).replace('/', '.').replace('.py', '')
        
        calls = self._extract_calls(node)
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        error_handling = self._extract_error_handling(node)
        
        source_lines = self.source_code.split('\n')
        start_line = node.lineno
        end_line = node.end_lineno or node.lineno
        code = ast.get_source_segment(self.source_code, node) or ""
        line_numbers = list(range(start_line, end_line + 1))
        
        return FunctionMetadata(
            name=node.name,
            lookup_id=lookup_id,
            file_path=self.file_path,
            repository_name=repo_name,
            module_name=module_name,
            nested_call_ids=[],
            start_line=start_line,
            end_line=end_line,
            code=code,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            class_context=self.current_class,
            calls=calls,
            imports=self.imports.copy(),
            decorators=decorators,
            error_handling=error_handling,
            line_numbers=line_numbers
        )

    def _extract_calls(self, node: ast.FunctionDef) -> List[str]:
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        return list(set(calls))

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        return "unknown"

    def _extract_error_handling(self, node: ast.FunctionDef) -> Dict[str, Any]:
        error_info = {'has_try_catch': False, 'error_types': [], 'try_catch_blocks': []}
        
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                error_info['has_try_catch'] = True
                try_catch_code = ast.get_source_segment(self.source_code, child)
                if try_catch_code:
                    error_info['try_catch_blocks'].append(try_catch_code.strip())
                
                for handler in child.handlers:
                    if handler.type and isinstance(handler.type, ast.Name):
                        error_info['error_types'].append(handler.type.id)
        
        return error_info
