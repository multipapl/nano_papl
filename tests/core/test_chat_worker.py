"""
Tests for ChatWorker.
Covers GenerationResult emission and execution flow.
"""
import pytest
from unittest.mock import MagicMock, patch
from core.models import GenerationConfig, GenerationResult


@pytest.fixture
def mock_llm_client():
    """Mock LLMClient to avoid real API calls."""
    with patch('core.workers.chat_worker.LLMClient') as mock:
        instance = mock.return_value
        instance.generate_chat.return_value = ("Test response", None)
        yield mock


class TestChatWorkerGenerationResult:
    """Tests for GenerationResult emission."""
    
    def test_chat_worker_emits_generation_result(self, qtbot, mock_llm_client):
        """Verify ChatWorker emits GenerationResult object."""
        from core.workers.chat_worker import ChatWorker
        
        config = GenerationConfig(model_id="test-model")
        worker = ChatWorker(
            api_key="test-key",
            config=config,
            history=[],
            user_message="Hello",
            session_id="test-session"
        )
        
        results = []
        worker.result_signal.connect(lambda r: results.append(r))
        
        with qtbot.waitSignal(worker.finished_signal, timeout=5000):
            worker.start()
        
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, GenerationResult)
        assert result.success is True
        assert result.text_response == "Test response"
        assert result.session_id == "test-session"
        assert result.model_id == "test-model"
    
    def test_chat_worker_generation_result_has_timing(self, qtbot, mock_llm_client):
        """Verify GenerationResult includes execution time."""
        from core.workers.chat_worker import ChatWorker
        
        config = GenerationConfig(model_id="test-model")
        worker = ChatWorker(
            api_key="test-key",
            config=config,
            history=[],
            user_message="Hello"
        )
        
        results = []
        worker.result_signal.connect(lambda r: results.append(r))
        
        with qtbot.waitSignal(worker.finished_signal, timeout=5000):
            worker.start()
        
        result = results[0]
        assert result.execution_time_ms >= 0
