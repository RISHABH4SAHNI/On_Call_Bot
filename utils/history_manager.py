import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

class HistoryManager:
    def __init__(self, history_file: str = "analysis_history.json"):
        self.history_file = Path(history_file)
        self.max_entries = 100
        self._ensure_history_file()
    
    def _ensure_history_file(self):
        if not self.history_file.exists():
            self._create_empty_history()
    
    def _create_empty_history(self):
        empty_history = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "total_analyses": 0,
            "analyses": []
        }
        self._save_history(empty_history)
    
    def _load_history(self) -> Dict[str, Any]:
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self._create_empty_history()
            return self._load_history()
    
    def _save_history(self, history: Dict[str, Any]):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def add_analysis(self, 
                    query: str, 
                    enhanced_query: str,
                    analysis_result: str,
                    confidence_score: float,
                    functions_analyzed: int,
                    embedding_service: str,
                    llm_service: str,
                    context: Optional[Dict[str, Any]] = None):
        
        history = self._load_history()
        
        analysis_entry = {
            "id": len(history["analyses"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "enhanced_query": enhanced_query,
            "analysis_result": analysis_result,
            "confidence_score": confidence_score,
            "functions_analyzed": functions_analyzed,
            "services_used": {
                "embedding": embedding_service,
                "llm": llm_service
            },
            "context": context or {}
        }
        
        history["analyses"].append(analysis_entry)
        history["total_analyses"] += 1
        history["last_updated"] = datetime.now().isoformat()
        
        if len(history["analyses"]) > self.max_entries:
            history["analyses"] = history["analyses"][-self.max_entries:]
        
        self._save_history(history)
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        history = self._load_history()
        return history["analyses"][-limit:]
    
    def get_all_analyses(self) -> List[Dict[str, Any]]:
        history = self._load_history()
        return history["analyses"]
    
    def get_statistics(self) -> Dict[str, Any]:
        history = self._load_history()
        analyses = history["analyses"]
        
        if not analyses:
            return {"total_analyses": 0, "average_confidence": 0.0}
        
        total_confidence = sum(a.get("confidence_score", 0) for a in analyses)
        avg_confidence = total_confidence / len(analyses)
        
        services_used = {}
        for analysis in analyses:
            services = analysis.get("services_used", {})
            embedding_service = services.get("embedding", "unknown")
            llm_service = services.get("llm", "unknown")
            
            key = f"{embedding_service}+{llm_service}"
            services_used[key] = services_used.get(key, 0) + 1
        
        return {
            "total_analyses": len(analyses),
            "average_confidence": round(avg_confidence, 3),
            "services_usage": services_used,
            "created_at": history.get("created_at"),
            "last_updated": history.get("last_updated")
        }
    
    def export_history(self, output_file: str):
        history = self._load_history()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def clear_history(self):
        self._create_empty_history()
