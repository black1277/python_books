import sys
import os

# Гарантируем, что корень проекта в PYTHONPATH
# (нужно для надёжности при запуске из IDE или ярлыка)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from library_app.main import launch_app

if __name__ == "__main__":
    launch_app()