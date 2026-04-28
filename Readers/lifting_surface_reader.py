import os
import math


def get_wing_data(file_path):
    """
    Read and parse a wing definition from a .txt file and return:
      - points_per_station: list of lists of (x,y,z) tuples,
      - n_stations: number of stations parsed,
      - error_flag: True if any parsing or geometry errors detected.
    """

    # --- SMART PATH LOGIC: FIXES FILE NOT FOUND ERROR ---
    # If the provided path is not absolute (e.g., "wing.txt"),
    # force it to look in the Project's "Files" folder.
    if not os.path.isabs(file_path):
        # Path to this specific file (Readers/lifting_surface_reader.py)
        current_reader_dir = os.path.dirname(os.path.abspath(__file__))
        # Up to KBE_2026 project root
        project_root = os.path.dirname(current_reader_dir)
        # Combine with "Files" folder and the requested filename
        file_path = os.path.join(project_root, "Files", file_path)

    def segments_intersect(p1, p2, p3, p4):
        # Ignore segments that only touch at endpoints
        if p1 in (p3, p4) or p2 in (p3, p4):
            return False

        def orient(a, b, c):
            return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

        def on_segment(a, b, c):
            return (min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and
                    min(a[1], b[1]) <= c[1] <= max(a[1], b[1]))

        o1, o2 = orient(p1, p2, p3), orient(p1, p2, p4)
        o3, o4 = orient(p3, p4, p1), orient(p3, p4, p2)

        if o1 * o2 < 0 and o3 * o4 < 0:
            return True
        if o1 == 0 and on_segment(p1, p2, p3):
            return True
        if o2 == 0 and on_segment(p1, p2, p4):
            return True
        if o3 == 0 and on_segment(p3, p4, p1):
            return True
        if o4 == 0 and on_segment(p3, p4, p2):
            return True

        return False

    def check_closed_and_simple(points):
        errors = []
        # Check if closed
        if points[0] != points[-1]:
            errors.append("Curve not closed: first and last points differ.")

        n = len(points)
        for i in range(n - 1):
            for j in range(i + 2, n - 1):
                if i == 0 and j == n - 2:
                    continue
                if segments_intersect(points[i], points[i + 1], points[j], points[j + 1]):
                    errors.append(f"Self-intersection between edges {i}-{i + 1} and {j}-{j + 1}.")
        return errors

    error_flag = False
    stations = []
    prev_y = -float('inf')

    # 1. Read lines with error handling
    try:
        with open(file_path, 'r') as f:
            raw = [ln.strip() for ln in f]
        lines = [ln for ln in raw if ln and not ln.startswith('#')]
    except Exception as e:
        print(f"Critical Reader Error: Could not open {file_path}. {e}")
        return [], 0, True

    # 2. Parsing logic
    i = 0
    while i < len(lines):
        parts = lines[i].split()
        if parts[0] != 'STATION' or len(parts) != 6:
            error_flag = True
            i += 1
            continue

        try:
            x, y, z, chord, twist = map(float, parts[1:])
        except ValueError:
            error_flag = True
            i += 1
            continue

        # station checks
        if any(abs(val) > 50 for val in (x, y, z)) or y < 0 or y <= prev_y or chord <= 0:
            error_flag = True

        prev_y = y
        i += 1

        if i >= len(lines) or lines[i] != 'AIRFOIL':
            error_flag = True
            continue
        i += 1

        airfoil = []
        while i < len(lines) and not lines[i].startswith('STATION'):
            try:
                xi, yi = map(float, lines[i].split())
                airfoil.append((xi, yi))
            except Exception:
                error_flag = True
                break
            i += 1

        if not airfoil:
            error_flag = True
            continue

        # Ensure closed
        if airfoil[0] != airfoil[-1]:
            airfoil.append(airfoil[0])

        errs = check_closed_and_simple(airfoil)
        if errs:
            error_flag = True

        stations.append({'LE': (x, y, z), 'chord': chord, 'twist': twist, 'airfoil': airfoil})

    if len(stations) < 2:
        error_flag = True

    # 3. Compute 3D points
    points_per_station = []
    for st in stations:
        x0, y0, z0 = st['LE']
        qc = 0.25 * st['chord']
        cos_t = math.cos(math.radians(st['twist']))
        sin_t = math.sin(math.radians(st['twist']))

        pts = []
        for xi, zi in st['airfoil']:
            xi_s, zi_s = xi * st['chord'], zi * st['chord']
            dx, dz = xi_s - qc, zi_s
            dx_r = dx * cos_t + dz * sin_t
            dz_r = -dx * sin_t + dz * cos_t
            pts.append((x0 + qc + dx_r, y0, z0 + dz_r))
        points_per_station.append(pts)

    return points_per_station, len(stations), error_flag