import pytest
import sys
import os

def main():
    """Скрипт для запуску тестів прямо з Python."""
    # Додаємо корінь проекту в шлях
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    print("Запуск тестів Nano_Papl...")
    # Викликаємо pytest з аргументами
    # -v: verbose
    # tests/: папка з тестами
    retcode = pytest.main(["-v", "tests/"])
    
    sys.exit(retcode)

if __name__ == "__main__":
    main()
