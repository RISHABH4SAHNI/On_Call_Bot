from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import openai
import requests
import os
from models.function_model import AnalysisRequest, AnalysisResult, SearchResult

class AnalysisService(ABC):
    @abstractmethod
    def analyze_issue(self, request: AnalysisRequest) -> AnalysisResult:
        pass

    @abstractmethod
    def request_additional_context(self, function_ids: List[str]) -> Dict[str, Any]:
        pass

class OpenAIAnalysisService(AnalysisService):
    def __init__(self, api_key: Optional[str] = None):
        self.client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.confidence_threshold = 0.8

    def analyze_issue(self, request: AnalysisRequest) -> AnalysisResult:
        context = self._build_analysis_context(request)
        
        analysis_prompt = f"""
You are a code expert analyzing an issue. Analyze the provided functions and determine if you have sufficient context.

Query: {request.enhanced_query}

Available Functions:
{context}

Provide analysis in this format:
CONFIDENCE_SCORE: [0.0-1.0]
ANALYSIS: [Your detailed analysis]
ISSUES_FOUND: [List specific code issues with line numbers]
SUGGESTED_FIXES: [Concrete code changes needed]
ADDITIONAL_CONTEXT_NEEDED: [List function lookup IDs if more context needed]
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior code expert who provides detailed technical analysis."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            return self._parse_analysis_response(response.choices[0].message.content, request)
        except Exception:
            return AnalysisResult(
                analysis="Analysis failed due to API error",
                confidence_score=0.0,
                functions_analyzed=len(request.functions),
                additional_context_needed=[],
                suggested_fixes=[]
            )

    def request_additional_context(self, function_ids: List[str]) -> Dict[str, Any]:
        return {"requested_function_ids": function_ids, "status": "pending"}

    def _build_analysis_context(self, request: AnalysisRequest) -> str:
        context_parts = []
        for i, result in enumerate(request.functions, 1):
            func = result.function_metadata
            context_parts.append(f"""
Function {i}: {func.name}
File: {func.file_path}
Lines: {func.start_line}-{func.end_line}
Lookup ID: {func.lookup_id}
Type: {'async' if func.is_async else 'sync'}
Calls: {', '.join(func.calls[:5])}
Error Handling: {'Yes' if func.error_handling.get('has_try_catch') else 'No'}
Code:
{func.code}
""")
        return '\n'.join(context_parts)

    def _parse_analysis_response(self, response: str, request: AnalysisRequest) -> AnalysisResult:
        lines = response.split('\n')
        confidence_score = 0.5
        analysis = response
        additional_context_needed = []
        suggested_fixes = []

        for line in lines:
            if line.startswith('CONFIDENCE_SCORE:'):
                try:
                    confidence_score = float(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith('ADDITIONAL_CONTEXT_NEEDED:'):
                context_part = line.split(':', 1)[1].strip()
                if context_part and context_part != 'None':
                    additional_context_needed = [id.strip() for id in context_part.split(',')]

        return AnalysisResult(
            analysis=analysis,
            confidence_score=confidence_score,
            functions_analyzed=len(request.functions),
            additional_context_needed=additional_context_needed,
            suggested_fixes=suggested_fixes
        )

class PerplexityAnalysisService(AnalysisService):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai"
        self.confidence_threshold = 0.8

    def analyze_issue(self, request: AnalysisRequest) -> AnalysisResult:
        context = self._build_analysis_context(request)
        
        prompt = f"Analyze this code issue: {request.enhanced_query}\n\nFunctions:\n{context}"
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 800,
                    "temperature": 0.1
                },
                timeout=30
            )
            
            if response.status_code == 200:
                analysis_text = response.json()['choices'][0]['message']['content']
                return AnalysisResult(
                    analysis=analysis_text,
                    confidence_score=0.7,
                    functions_analyzed=len(request.functions),
                    additional_context_needed=[],
                    suggested_fixes=[]
                )
        except Exception:
            pass
        
        return AnalysisResult(
            analysis="Analysis failed",
            confidence_score=0.0,
            functions_analyzed=len(request.functions),
            additional_context_needed=[],
            suggested_fixes=[]
        )

    def request_additional_context(self, function_ids: List[str]) -> Dict[str, Any]:
        return {"requested_function_ids": function_ids, "status": "pending"}

    def _build_analysis_context(self, request: AnalysisRequest) -> str:
        context_parts = []
        for result in request.functions:
            func = result.function_metadata
            context_parts.append(f"{func.name} in {func.file_path}: {func.code[:200]}...")
        return '\n'.join(context_parts)

class OllamaAnalysisService(AnalysisService):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.confidence_threshold = 0.8

    def analyze_issue(self, request: AnalysisRequest) -> AnalysisResult:
        context = self._build_analysis_context(request)
        prompt = f"Analyze this code issue: {request.enhanced_query}\n\nCode:\n{context}"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": "codellama:7b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "max_tokens": 800}
                },
                timeout=60
            )
            
            if response.status_code == 200:
                analysis_text = response.json().get('response', 'No analysis available')
                return AnalysisResult(
                    analysis=analysis_text,
                    confidence_score=0.6,
                    functions_analyzed=len(request.functions),
                    additional_context_needed=[],
                    suggested_fixes=[]
                )
        except Exception:
            pass
        
        return AnalysisResult(
            analysis="Analysis failed",
            confidence_score=0.0,
            functions_analyzed=len(request.functions),
            additional_context_needed=[],
            suggested_fixes=[]
        )

    def request_additional_context(self, function_ids: List[str]) -> Dict[str, Any]:
        return {"requested_function_ids": function_ids, "status": "pending"}

    def _build_analysis_context(self, request: AnalysisRequest) -> str:
        context_parts = []
        for result in request.functions:
            func = result.function_metadata
            context_parts.append(f"{func.name}: {func.code}")
        return '\n'.join(context_parts)
