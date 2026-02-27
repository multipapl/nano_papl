import os
import subprocess
import sys
import shutil


def main():
    print("--- Nano Papl Builder ---")
    
    # Set CWD to project root (parent of scripts folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    print(f"Working in: {project_root}")

    # Import constants for version
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        
    from core import constants
    exe_name = f"{constants.APP_NAME} v{constants.APP_VERSION}"
    print(f"Building: {exe_name}")
    
    # Define data separator (semicolon for Windows)
    sep = ";" if os.name == 'nt' else ":"
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",  # No console window
        "--name", exe_name,
        "--icon", os.path.join("assets", "ico.ico"),
        f"--add-data", f"assets{sep}assets",
        f"--add-data", f"data{sep}data",
        "main.py"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.call(cmd)
    
    if result == 0:
        # Cleanup build folder
        shutil.rmtree("build", ignore_errors=True)
        print(f"\n✅ [SUCCESS] Build complete!")
        print(f"   EXE: dist/{exe_name}.exe")
    else:
        print(f"\n❌ [ERROR] Build failed with code {result}")
        return result
    
    return 0


if __name__ == "__main__":
    exit(main())
