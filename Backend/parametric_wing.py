import math
from parapy.core import Input, Part, Attribute
from parapy.geom import GeomBase, FittedCurve, Point, LoftedSolid


class ParametricWing(GeomBase):
    """Parametric wing generator using 2D airfoil data and swept trapezoidal sections."""

    wing_file = Input()  # Expects a 2D Airfoil coordinate file (.dat or .txt)
    is_vertical = Input(False)

    # Absolute positions in meters
    abs_x = Input(0.0)
    abs_z = Input(0.0)

    # Parametric Geometry Inputs
    dihedral = Input(5.0)
    root_chord = Input(4.5)
    sections = Input([{"span": 8.0, "tip_chord": 1.5, "sweep": 40.0}])

    @Attribute
    def error_lifting_surface(self):
        """Tells the IntersectionChecker if the airfoil file failed to load."""
        try:
            with open(self.wing_file, 'r') as f:
                return False
        except FileNotFoundError:
            return True

    @Attribute
    def normalized_airfoil_points(self):
        points = []
        try:
            with open(self.wing_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        try:
                            x = float(parts[0])
                            z = float(parts[1])
                            points.append(Point(x, 0.0, z))
                        except ValueError:
                            pass

            # --- CRITICAL CAD FIX: THE TRAILING EDGE SEAL ---
            # Airfoil files almost always have an open trailing edge.
            # We MUST force the last coordinate to equal the first coordinate.
            # This creates a perfect sharp edge, destroying the "micro-face"
            if len(points) > 2:
                distance = points[0].distance(points[-1])
                # If there is any gap at all, stitch the end to the beginning
                if distance > 1e-7:
                    points.append(points[0])

        except FileNotFoundError:
            # Fallback diamond shape (closed loop)
            points = [Point(0, 0, 0), Point(0.5, 0, 0.1), Point(1, 0, 0), Point(0, 0, 0)]

        return points

    @Part(parse=False)
    def airfoil_curves(self):
        rib_curves = []
        current_x = self.abs_x
        current_y = -0.05
        current_z = self.abs_z

        # Gets the Root Chord, then grabs the Tip Chord for every section added
        chords = [self.root_chord] + [sec["tip_chord"] for sec in self.sections]

        for i, chord in enumerate(chords):
            scaled_points = []

            for p in self.normalized_airfoil_points:
                # 1. Scale the raw 2D airfoil by the chord
                px = p.x * chord
                pz = p.z * chord  # This is the physical thickness

                # 2. Add the absolute position shifts DIRECTLY to the points
                if self.is_vertical:
                    # Vertical tail stands up: Span goes UP (Z), thickness goes LEFT/RIGHT (Y)
                    pt = Point(current_x + px, current_y + pz, current_z)
                else:
                    # Main wing lays flat: Span goes OUT (Y), thickness goes UP/DOWN (Z)
                    pt = Point(current_x + px, current_y, current_z + pz)

                scaled_points.append(pt)

            # 3. Create the curve. ParaPy now physically cannot draw it at Y=0!
            curve = FittedCurve(points=scaled_points)
            rib_curves.append(curve)

            # 4. Calculate the starting position for the NEXT rib
            if i < len(self.sections):
                sec = self.sections[i]
                if self.is_vertical:
                    current_z += sec["span"]  # Span goes UP
                    current_x += sec["span"] * math.tan(math.radians(sec["sweep"]))
                else:
                    current_y += sec["span"]  # Span goes OUT
                    current_x += sec["span"] * math.tan(math.radians(sec["sweep"]))
                    current_z += sec["span"] * math.tan(math.radians(self.dihedral))

        return rib_curves

    @Part(parse=False)
    def solid(self):
        return LoftedSolid(
            profiles=self.airfoil_curves,
            ruled=True,
            color="red" if self.is_vertical else "yellow",
            transparency=0.2
        )