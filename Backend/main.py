import sys
import os

# 1. Force Python to recognize the main KBE_2026 folder
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 2. NOW you can do your imports
from Backend.aircraft import Aircraft

from parapy.gui import display
from aircraft import Aircraft

if __name__ == "__main__":
    ac = Aircraft()
    display(ac)