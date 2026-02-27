import pytest
from core.workers.base_worker import BaseWorker

class MockWorker(BaseWorker):
    def __init__(self, should_fail=False):
        super().__init__()
        self.should_fail = should_fail
        self.executed = False

    def execute(self):
        self.executed = True
        if self.should_fail:
            raise ValueError("Test Failure")
        self.result_signal.emit("Success")

def test_base_worker_success(qtbot):
    worker = MockWorker(should_fail=False)
    
    results = []
    worker.result_signal.connect(results.append)
    
    with qtbot.waitSignal(worker.finished_signal, timeout=2000):
        worker.start()
    
    assert worker.executed is True
    assert results == ["Success"]
    assert worker.is_running is False

def test_base_worker_failure(qtbot):
    worker = MockWorker(should_fail=True)
    
    errors = []
    worker.error_signal.connect(errors.append)
    
    with qtbot.waitSignal(worker.finished_signal, timeout=2000):
        worker.start()
    
    assert worker.executed is True
    assert errors == ["Test Failure"]
    assert worker.is_running is False

def test_base_worker_stop():
    worker = BaseWorker()
    assert worker.is_running is True
    worker.stop()
    assert worker.is_running is False
