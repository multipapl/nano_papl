import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path.cwd()))

def verify():
    print("--- Verifying Refactoring ---")
    
    try:
        print("1. Testing PathProvider...")
        from core.utils.path_provider import PathProvider
        pp = PathProvider()
        print(f"   Root: {pp.get_app_root()}")
        print("   [OK]")
        
        print("2. Testing GenerationService...")
        from core.services.generation_service import GenerationService
        gs = GenerationService(api_key="test_key")
        print("   [OK]")
        
        print("3. Testing LLMFactory & Client...")
        from core.factories.llm_factory import LLMProviderFactory, GeminiProvider
        from core.llm_client import LLMClient
        client = LLMClient("gemini", "model-id", "api_key")
        print("   [OK]")
        
        print("4. Testing ComfyOrchestrator...")
        from core.services.comfy_orchestrator import ComfyOrchestrator
        # Mock settings
        settings = {"comfy_url": "http://localhost:8188"}
        orch = ComfyOrchestrator(settings)
        print("   [OK]")
        
        print("5. Testing Workers Imports...")
        from core.workers.batch_worker import BatchWorker
        from core.workers.chat_worker import ChatWorker
        from core.workers.comfy_worker import ComfyWorker
        print("   [OK]")
        
        print("\n--- ALL CHECKS PASSED ---")
        
    except ImportError as e:
        print(f"\n[FAIL] Import Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Runtime Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
