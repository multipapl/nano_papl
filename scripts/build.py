import os
import subprocess
import sys
from PIL import Image

def main():
    print("--- Nano Papl Builder ---")
    
    # Set CWD to project root (parent of scripts folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    print(f"Working in: {project_root}")

    # 1. Convert Icon
    if os.path.exists(os.path.join("assets", "icon.png")):
        print("[1/2] Converting assets/icon.png to assets/icon.ico...")
        img = Image.open(os.path.join("assets", "icon.png"))
        img.save(os.path.join("assets", "icon.ico"), format='ICO', sizes=[(256, 256)])
    else:
        print("WARNING: assets/icon.png not found!")

    # 2. Run PyInstaller
    print("[2/2] Running PyInstaller...")
    
    # Define data separator (semicolon for Windows)
    sep = ";" if os.name == 'nt' else ":"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed", # No console
        "--name", "Nano Papl v1.1",
        "--icon", os.path.join("assets", "icon.ico"),
        f"--add-data", f"assets{sep}assets",
        f"--add-data", f"data{sep}data",
        "main.py"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    subprocess.call(cmd)
    
    print("\n[SUCCESS] Build complete! Check 'dist' folder.")

if __name__ == "__main__":
    main()
