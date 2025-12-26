import os
import subprocess
import sys
from PIL import Image

def main():
    print("--- Nano Papl Builder ---")
    
    # 1. Convert Icon
    if os.path.exists("icon.png"):
        print("[1/2] Converting icon.png to icon.ico...")
        img = Image.open("icon.png")
        img.save("icon.ico", format='ICO', sizes=[(256, 256)])
    else:
        print("WARNING: icon.png not found!")

    # 2. Run PyInstaller
    print("[2/2] Running PyInstaller...")
    
    # Define data separator (semicolon for Windows)
    sep = ";" if os.name == 'nt' else ":"
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed", # No console
        "--name", "Nano Papl",
        "--icon", "icon.ico",
        f"--add-data", f"icon.png{sep}.",
        f"--add-data", f"templates.json{sep}.",
        "main.py"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    subprocess.call(cmd)
    
    print("\n[SUCCESS] Build complete! Check 'dist' folder.")

if __name__ == "__main__":
    main()
