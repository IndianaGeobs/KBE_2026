import os
import json
import numpy as np


def get_fuselage_data(filename, *, tol=1e-2):
    """
    Reads fuselage data from a JSON file and validates the values,
    raising an error flag on any error.
    """

    print(f"DEBUG: Reader is currently attempting to open: {filename}")
    error_reading_fuselage = False

    # If the filename is not an absolute path, force it to look in KBE_2026/Files
    if not os.path.isabs(filename):
        # Path to this specific file (Readers/fuselage_reader.py)
        current_reader_dir = os.path.dirname(os.path.abspath(__file__))
        # Up to KBE_2026 project root
        project_root = os.path.dirname(current_reader_dir)
        # Combine with "Files" folder and the requested filename
        filename = os.path.join(project_root, "Files", filename)

    # 1. Read the JSON file
    try:
        with open(filename, 'r') as f:
            data = json.load(f)

        sections = data.get("cross_sections", [])

        # 2. Extract columns into numpy arrays
        xs = np.array([sec["station"] for sec in sections])
        radii = np.array([sec["nominal_radius"] for sec in sections])
        min_r = np.array([sec["min_radius"] for sec in sections])
        max_r = np.array([sec["max_radius"] for sec in sections])
        length = float(xs[-1]) if xs.size > 0 else 0.0

    except Exception as e:
        print(f"Error loading JSON from {filename}: {e}")
        error_reading_fuselage = True
        xs = radii = min_r = max_r = np.empty(0)
        length = 0.0

    # 3. Validate shape and station count
    if len(xs) < 10:
        error_reading_fuselage = True

    # 4. Length and endpoints checks
    if length > 100.0 or xs.size == 0 or xs[0] != 0:
        print('a')
        error_reading_fuselage = True

    # 5. Spacing check: strictly increasing and equispaced
    if xs.size > 1:
        diffs = np.diff(xs)
        if np.any(diffs <= 0):
            print('b')
            error_reading_fuselage = True

        # Check equispacing to relative tol
        expected = length / (len(xs) - 1)
        rel_dev = np.abs(diffs - expected) / expected
        if np.max(rel_dev) > tol:
            print('c')
            error_reading_fuselage = True

    # 6. Radius checks (start and end must be 0, middle must be > 0)
    if radii.size == 0 or radii[0] != 0 or radii[-1] != 0 or np.any(radii[1:-1] <= 0):
        print('d')
        error_reading_fuselage = True

    # 7. Min/max radius boundary checks
    if min_r.size > 0 and (np.any(min_r < 0) or np.any(min_r > radii)):
        print('e')
        error_reading_fuselage = True

    if max_r.size > 0 and (np.any(max_r < radii) or np.any(max_r > 5)):
        print('f')
        error_reading_fuselage = True

    return xs, radii, min_r, max_r, length, error_reading_fuselage