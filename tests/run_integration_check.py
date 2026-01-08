import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.services.generation_service import GenerationService

class IntegrationSmokeTest(unittest.TestCase):
    def test_full_cycle_dry_run(self):
        """
        Simulates a full cycle:
        1. Setup Prompt Data
        2. Setup Configuration
        3. Call Generation Service (Mocked API)
        4. Verify Output Path interaction
        """
        print("\n--- Starting Integration Smoke Test ---")
        
        # 1. Setup Data
        prompt_data = {
            "title": "SmokeTest",
            "prompt": "A test prompt"
        }
        
        # Temp dir for output
        out_dir = Path("temp_integration_test")
        out_dir.mkdir(exist_ok=True)
        
        config = {
            "resolution": "1K",
            "ratio": "1:1",
            "format": "PNG",
            "project_out_dir": out_dir,
            "save_log": True
        }
        
        # Source image
        src_image = Path("dummy_source.png")
        # Ensure dummy source exists or mock open
        
        print("1. Data Setup Complete")
        
        # 2. Service Init
        service = GenerationService("dummy_key")
        
        # 3. Mock Internals to avoid Real API & IO
        with patch.object(service, "client") as mock_client, \
             patch('core.services.generation_service.Image.open') as mock_open:
             
            # Setup Mock Response from API
            mock_response = MagicMock()
            mock_part = MagicMock()
            mock_part.inline_data.data = b"fake_bytes"
            mock_response.parts = [mock_part]
            mock_client.models.generate_content.return_value = mock_response
            
            # Setup Mock Image Open (Source)
            mock_src = MagicMock()
            mock_src.size = (1024, 1024)
            mock_src.format = "PNG"
            mock_open.return_value.__enter__.return_value = mock_src
            
            # Setup Mock Image Open (Generated) - tricky as it opens bytes
            # We can mock _save_generated_image to verify it receives correct data
            # OR we can mock Image.open to return different mocks for different calls.
            
            print("2. Service Initialized & Mocked")
            
            # Use a side_effect for Image.open to handle source vs generated
            # But simplest is to mock _save_generated_image to ensure we reached that step
            with patch.object(service, '_save_generated_image') as mock_save:
                mock_save.return_value = {'success': True}
                
                print("3. Executing Generation...")
                result = service.generate_image(prompt_data, src_image, config)
                
                print(f"4. Result: {result}")
                
                self.assertTrue(result['success'])
                mock_client.models.generate_content.assert_called()
                mock_save.assert_called()
                
        # Cleanup
        if out_dir.exists():
            import shutil
            shutil.rmtree(out_dir)
            
        print("--- Integration Smoke Test Passed ---")

if __name__ == "__main__":
    unittest.main()
