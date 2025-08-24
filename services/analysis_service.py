from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import openai
import requests
import os
from models.function_model import AnalysisRequest, AnalysisResult, SearchResult, AnalysisApproach

class AnalysisService(ABC):
    @abstractmethod
    def analyze_issue(self, request: AnalysisRequest) -> AnalysisResult:
        pass

class OpenAIAnalysisService(AnalysisService):
    def __init__(self, api_key: Optional[str] = None):
        self.client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.confidence_threshold = 0.8

    def analyze_issue(self, request: AnalysisRequest) -> AnalysisResult:
        context = self._build_analysis_context(request)
        
        if request.approach == AnalysisApproach.CALL_GRAPH:
            analysis_prompt = self._build_call_graph_prompt(request, context)
        else:
            analysis_prompt = self._build_lookup_table_prompt(request, context)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior code expert who provides detailed technical analysis with exact line number references."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            return self._parse_analysis_response(response.choices[0].message.content, request)
        except Exception:
            return AnalysisResult(
                analysis="Analysis failed due to API error",
                confidence_score=0.0,
                functions_analyzed=len(request.functions),
                additional_context_needed=[],
                suggested_fixes=[],
                approach_used=request.approach
            )

    def _build_lookup_table_prompt(self, request: AnalysisRequest, context: str) -> str:
        return f"""
You are a code expert analyzing an issue using FUNCTION LOOKUP TABLE approach. 
Analyze the provided functions and their nested dependencies to identify the root cause.

Query: {request.enhanced_query}

Available Functions with Dependencies:
{context}

IMPORTANT: Reference exact line numbers from the code when identifying issues.

Provide your analysis in this format:
CONFIDENCE_SCORE: [0.0-1.0]
ANALYSIS: [Detailed analysis with exact line number references]
ISSUES_FOUND: [List specific issues with file:line format]
SUGGESTED_FIXES: [Concrete fixes with line numbers]
ADDITIONAL_CONTEXT_NEEDED: [List function lookup IDs if more context needed]
"""

    def _build_call_graph_prompt(self, request: AnalysisRequest, context: str) -> str:
        call_graph_info = ""
        if request.call_graph_context:
            call_graph_info = f"\nCall Graph Context:\n{request.call_graph_context}"

        return f"""
You are a code expert analyzing an issue using CALL GRAPH approach.
Use the call graph to understand function dependencies and execution flow.

Query: {request.enhanced_query}

Primary Functions and Their Call Graph Context:
{context}
{call_graph_info}

IMPORTANT: Leverage the call graph to trace execution flow and identify cascading issues.
Reference exact line numbers when identifying problems.

Provide your analysis in this format:
CONFIDENCE_SCORE: [0.0-1.0]
ANALYSIS: [Analysis considering call graph dependencies with line numbers]
GRAPH_INSIGHTS: [How the call graph reveals the issue]
ISSUES_FOUND: [Issues with execution flow and line references]
SUGGESTED_FIXES: [Fixes considering dependency impact]
ADDITIONAL_CONTEXT_NEEDED: [List function lookup IDs if more context needed]
"""

    def _build_analysis_context(self, request: AnalysisRequest) -> str:
        context_parts = []
        
        for i, result in enumerate(request.functions, 1):
            func = result.function_metadata
            context_parts.append(f"""
Function {i}: {func.name}
File: {func.file_name} ({func.file_path})
Lines: {func.start_line}-{func.end_line}
Lookup ID: {func.lookup_id}
Type: {'async' if func.is_async else 'sync'}
Class: {func.class_context or 'None'}
Decorators: {', '.join(func.decorators) if func.decorators else 'None'}
Calls: {', '.join(func.calls[:10]) if func.calls else 'None'}
Error Handling: {'Yes' if func.error_handling.get('has_try_catch') else 'No'}

Code with line numbers:
{func.code_with_line_numbers}
""")

            if hasattr(result, 'nested_functions') and result.nested_functions:
                if request.approach == AnalysisApproach.FUNCTION_LOOKUP_TABLE:
                    context_parts.append(f"\nNested Function Dependencies for {func.name}:")
                    for nested_id, nested_info in result.nested_functions.items():
                        if isinstance(nested_info, dict) and 'function_name' in nested_info:
                            context_parts.append(f"  - {nested_info['function_name']} ({nested_info.get('file_path', 'Unknown')})")
                
                elif request.approach == AnalysisApproach.CALL_GRAPH:
                    if 'call_graph_context' in result.nested_functions:
                        graph_context = result.nested_functions['call_graph_context']
                        context_parts.append(f"\nCall Graph Context for {func.name}:")
                        context_parts.append(f"  - Dependencies: {graph_context.get('dependency_count', 0)}")
                        context_parts.append(f"  - Graph Depth: {graph_context.get('graph_depth', 0)}")
                        context_parts.append(f"  - Files Involved: {', '.join(graph_context.get('files_involved', []))}")
                        context_parts.append(f"  - Has Error Handling: {graph_context.get('has_error_handling', False)}")
        
        return '\n'.join(context_parts)

    def _parse_analysis_response(self, response: str, request: AnalysisRequest) -> AnalysisResult:
        lines = response.split('\n')
        confidence_score = 0.5
        analysis = response
        additional_context_needed = []
        suggested_fixes = []
        graph_context = {}

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
            elif line.startswith('GRAPH_INSIGHTS:') and request.approach == AnalysisApproach.CALL_GRAPH:
                graph_context['insights'] = line.split(':', 1)[1].strip()
            elif line.startswith('SUGGESTED_FIXES:'):
                fixes_part = line.split(':', 1)[1].strip()
                if fixes_part and fixes_part != 'None':
                    suggested_fixes = [{"description": fix.strip(), "type": "code_change"} for fix in fixes_part.split(';')]

        return AnalysisResult(
            analysis=analysis,
            confidence_score=confidence_score,
            functions_analyzed=len(request.functions),
            additional_context_needed=additional_context_needed,
            suggested_fixes=suggested_fixes,
            approach_used=request.approach,
            graph_context=graph_context if graph_context else None
        )

class PerplexityAnalysisService(AnalysisService):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai"
        self.confidence_threshold = 0.8

    def analyze_issue(self, request: AnalysisRequest) -> AnalysisResult:
        context = self._build_analysis_context(request)
        
        if request.approach == AnalysisApproach.CALL_GRAPH:
            prompt = f"Analyze this code issue using call graph approach: {request.enhanced_query}\n\nFunctions with call graph:\n{context}"
        else:
            prompt = f"Analyze this code issue using lookup table approach: {request.enhanced_query}\n\nFunctions:\n{context}"
        
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
                    "max_tokens": 1200,
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
                    suggested_fixes=[],
                    approach_used=request.approach,
                    graph_context=None
                )
        except Exception:
            pass
        
        return AnalysisResult(
            analysis="Analysis failed",
            confidence_score=0.0,
            functions_analyzed=len(request.functions),
            additional_context_needed=[],
            suggested_fixes=[],
            approach_used=request.approach,
            graph_context=None
        )

    def _build_analysis_context(self, request: AnalysisRequest) -> str:
        context_parts = []
        for result in request.functions:
            func = result.function_metadata
            context_parts.append(f"""
{func.name} in {func.file_name}:
Lines {func.start_line}-{func.end_line}
{func.code_with_line_numbers[:500]}...
""")
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
                    "options": {"temperature": 0.1, "max_tokens": 1200}
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
                    suggested_fixes=[],
                    approach_used=request.approach,
                    graph_context=None
                )
        except Exception:
            pass
        
        return AnalysisResult(
            analysis="Analysis failed",
            confidence_score=0.0,
            functions_analyzed=len(request.functions),
            additional_context_needed=[],
            suggested_fixes=[],
            approach_used=request.approach,
            graph_context=None
        )

    def _build_analysis_context(self, request: AnalysisRequest) -> str:
        context_parts = []
        for result in request.functions:
            func = result.function_metadata
            context_parts.append(f"""
{func.name} in {func.file_name}:
{func.code_with_line_numbers}
""")
        return '\n'.join(context_parts)
