import os
import matlab.engine
from parapy.webgui.core import display
from app import App

# 1) Workspace cleanup
cwd = os.getcwd()
files_to_keep = [
    "wing.txt", "hor_tail.txt", "vert_tail.txt", "fuselage.txt",
    "wing_default.txt", "hor_tail_default.txt", "vert_tail_default.txt", "fuselage_default.txt"
]

for filename in os.listdir(cwd):
    if filename.endswith(".txt") and filename not in files_to_keep:
        try:
            os.remove(os.path.join(cwd, filename))
        except Exception as e:
            print(f"Error deleting {filename}: {e}")

# 2) Start MATLAB engine once globally
eng = matlab.engine.start_matlab()

# 3) Start Application
if __name__ == "__main__":
    display(App, reload=True)