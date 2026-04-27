import numpy as np

def get_fuselage_data(filename, *, tol=1e-2):
    """
    Reads fuselage data from a text file and validates the columns, raising an error flag on any error.

    Expected file columns (in order):
        [0] x_station    (must go from 0 up to ≤ 100, equispaced)
        [1] radius       (nominal)
        [2] min_radius   (must satisfy 0 ≤ min_radius ≤ radius)
        [3] max_radius   (must satisfy radius ≤ max_radius ≤ 5)

    Additional checks:
        - At least 10 stations (rows) must be present.
        - radius[0] and radius[-1] must both be exactly 0.
        - x_stations must be strictly increasing and equispaced within ±tol fraction.

    Parameters
    ----------
    filename : str
        Path to the fuselage data text file.
    tol : float
        Maximum allowed relative deviation from perfect spacing (e.g., tol=1e-3 allows 0.1%).

    Returns
    -------
    fuselage_x_stations : np.ndarray
    fuselage_radii      : np.ndarray
    fuselage_min_radii  : np.ndarray
    fuselage_max_radii  : np.ndarray
    fuselage_length     : float
    error_reading_fuselage : bool
    """
    error_reading_fuselage = False

    # 1. Read & filter out blank lines / comments
    try:
        with open(filename, 'r') as f:
            lines = [ln for ln in f if ln.strip() and not ln.strip().startswith('#')]
    except Exception:
        error_reading_fuselage = True
        lines = []

    if not lines:
        data = np.empty((0, 4))
    else:
        try:
            data = np.loadtxt(lines)
        except Exception:
            error_reading_fuselage = True
            data = np.empty((0, 4))

    # Validate shape and station count
    if data.ndim != 2 or data.shape[1] < 4 or data.shape[0] < 10:
        error_reading_fuselage = True

    # Extract columns
    xs = data[:, 0] if data.size else np.empty(0)
    radii = data[:, 1] if data.shape[1] >= 2 else np.empty(0)
    min_r = data[:, 2] if data.shape[1] >= 3 else np.empty(0)
    max_r = data[:, 3] if data.shape[1] >= 4 else np.empty(0)
    length = float(xs[-1]) if xs.size else 0.0

    # Length and endpoints
    if length > 100.0 or xs.size == 0 or xs[0] != 0:
        print('a')
        error_reading_fuselage = True

    # Spacing check: strictly increasing
    diffs = np.diff(xs)
    if np.any(diffs <= 0):
        print('b')
        error_reading_fuselage = True

    # Check equispacing to relative tol
    if diffs.size > 1:
        expected = length / (len(xs) - 1)
        rel_dev = np.abs(diffs - expected) / expected
        if np.max(rel_dev) > tol:
            print('c')
            error_reading_fuselage = True

    # Radius checks
    if radii.size == 0 or radii[0] != 0 or radii[-1] != 0 or np.any(radii[1:-1] <= 0):
        print('d')
        error_reading_fuselage = True

    # Min/max radius checks
    if np.any(min_r < 0) or np.any(min_r > radii):
        print('e')
        error_reading_fuselage = True
    if np.any(max_r < radii) or np.any(max_r > 5):
        print('f')
        error_reading_fuselage = True

    return xs, radii, min_r, max_r, length, error_reading_fuselage
