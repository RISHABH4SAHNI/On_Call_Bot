import pytest
from unittest.mock import Mock, patch
from core.workflow_engine import WorkflowEngine

class TestWorkflowEngine:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.engine = WorkflowEngine(
            embedding_service_type="openai",
            llm_service_type="openai"
        )
    
    def test_workflow_engine_initialization(self):
        """Test workflow engine initializes correctly"""
        assert self.engine.embedding_service_type == "openai"
        assert self.engine.llm_service_type == "openai"
        assert self.engine.service_factory is not None
        assert self.engine.history_manager is not None
    
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_process_repository_invalid_path(self, mock_isdir, mock_exists):
        """Test repository processing with invalid path"""
        mock_exists.return_value = False
        
        with pytest.raises(ValueError, match="Repository path does not exist"):
            self.engine.process_repository("/invalid/path")
    
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_process_repository_not_directory(self, mock_isdir, mock_exists):
        """Test repository processing with file instead of directory"""
        mock_exists.return_value = True
        mock_isdir.return_value = False
        
        with pytest.raises(ValueError, match="Path is not a directory"):
            self.engine.process_repository("/path/to/file.py")
    
    def test_analyze_user_issue_empty_query(self):
        """Test analysis with empty query"""
        result = self.engine.analyze_user_issue("")
        assert "error" in result
        assert result["error"] == "Query cannot be empty"
    
    def test_validate_services(self):
        """Test service validation"""
        validation = self.engine.validate_services()
        assert isinstance(validation, dict)
        assert "embedding_service" in validation
        assert "search_service" in validation
        assert "query_enhancer" in validation
        assert "analysis_service" in validation
