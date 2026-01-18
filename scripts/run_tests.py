"""
Run tests for Nano Papl.
Cleans up coverage files after execution.
"""
import pytest
import sys
import os


def main():
    """Run tests and cleanup coverage files."""
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    os.chdir(project_root)
    
    print("Запуск тестів Nano_Papl...")
    retcode = pytest.main(["-v", "tests/"])
    
    # Cleanup .coverage file
    coverage_file = os.path.join(project_root, ".coverage")
    if os.path.exists(coverage_file):
        os.remove(coverage_file)
        print("\n🧹 Cleanup: .coverage file removed")
    
    sys.exit(retcode)


if __name__ == "__main__":
    main()
