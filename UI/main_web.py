import os
import sys

# 1. The exact folder paths
vsp_root = r"C:\Users\bassg\OpenVSP-3.50.0-win64"
vsp_deep = r"C:\Users\bassg\OpenVSP-3.50.0-win64\python\openvsp\openvsp"

# 2. Add DLL directories
if hasattr(os, 'add_dll_directory'):
    os.add_dll_directory(vsp_root)
    os.add_dll_directory(vsp_deep)

    # Python .venv safety net
    if hasattr(sys, 'base_prefix'):
        os.add_dll_directory(sys.base_prefix)
        base_bin = os.path.join(sys.base_prefix, 'Library', 'bin')
        if os.path.exists(base_bin):
            os.add_dll_directory(base_bin)

# 3. Add the ONE deep folder to Python's map so it finds vsp.py
if vsp_deep not in sys.path:
    sys.path.insert(0, vsp_deep)

# 4. Direct Import (No ghost config files!)
import vsp

vsp.VSPCheckSetup()
print(f"Success! Linked to VSP Version: {vsp.GetVSPVersion()}")

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from parapy.webgui.core import display
from app import App

import matlab.engine


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