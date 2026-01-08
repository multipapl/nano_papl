import subprocess
import sys
import webbrowser
from pathlib import Path

def run_tests():
    print("="*60)
    print("Running NanoPapl Test Suite")
    print("="*60)

    # 1. Run Core & UI Unit Tests with Coverage
    print("\n[1/3] Running Unit Tests (Core & UI)...")
    exit_code_pytest = subprocess.call([
        sys.executable, "-m", "pytest",
        "--cov=core", "--cov=ui", "--cov-report=html:cov_html", 
        "tests/"
    ])

    if exit_code_pytest != 0:
        print("\n!!! Unit Tests FAILED !!!")
        # We don't exit yet, we want to see integration results if possible or stop here.
        # Usually stop on unit failure.
        return exit_code_pytest

    # 2. Run Integration Smoke Test
    print("\n[2/3] Running Integration Smoke Tests...")
    exit_code_integration = subprocess.call([
        sys.executable, "tests/run_integration_check.py"
    ])

    if exit_code_integration != 0:
        print("\n!!! Integration Tests FAILED !!!")
        return exit_code_integration

    print("\n" + "="*60)
    print("ALL TESTS PASSED")
    print("="*60)
    
    # 3. Open Report
    report_path = Path("cov_html/index.html").absolute()
    if report_path.exists():
        print(f"Opening coverage report: {report_path}")
        webbrowser.open(report_path.as_uri())
    
    return 0

if __name__ == "__main__":
    sys.exit(run_tests())
