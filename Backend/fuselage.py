import os
import sys
import numpy as np
from math import radians

# Get the directory of the current script (the 'Backend' folder)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Go up one level to the main project folder ('KBE_2026')
parent_dir = os.path.dirname(current_dir)

# Add the main folder to Python's map so it can find the 'Readers' package
sys.path.append(parent_dir)
from Readers.fuselage_reader import get_fuselage_data

# Build the path directly to the 'Files' folder for your text file
DEFAULT_FUSELAGE = os.path.join(parent_dir, "Files", "fuselage.json")

from parapy.core import Part, Attribute, Input, child
from parapy.geom import GeomBase, Point, FittedCurve, Revolution, RotatedShape, Vector, Circle, translate, Wire, LineSegment, Face, RevolvedSolid


class Fuselage(GeomBase):
    """
    ParaPy GeomBase for creating a fuselage by revolving a radial profile
    loaded from a text file.
    """

    # Percentage inputs (0.0 to 1.0)
    start_perc = Input(0.0)
    end_perc = Input(1.0)


    fuselage_data = Input()
    fuselage_file = Input(DEFAULT_FUSELAGE)
    show_constraints = Input(False)
    error_reading_fuselage = Input(False)
    max_revolution_curve_degree = Input(8)

    @Attribute
    def sliced_data(self):
        xs, rs, min_r, max_r, length, err = self.fuselage_data

        x_start = self.start_perc * length
        x_end = self.end_perc * length

        # This is the "Master Radius" for the cylinder connections
        cyl_radius = float(max(rs))

        # Identify which section we are currently building
        is_nose = self.start_perc < 0.05
        is_tail = self.end_perc > 0.95
        is_main_body = not is_nose and not is_tail

        if is_main_body:
            # Force perfect cylinder
            xs_clean = [x_start, x_end]
            rs_clean = [cyl_radius, cyl_radius]

        elif is_nose:
            # Interpolate normally, but FORCE the last point to match the cylinder
            r_start = float(np.interp(x_start, xs, rs))
            mask = (xs > x_start + 1e-5) & (xs < x_end - 1e-5)
            xs_clean = [x_start] + xs[mask].tolist() + [x_end]
            rs_clean = [r_start] + rs[mask].tolist() + [cyl_radius]  # Forced match

        elif is_tail:
            # Interpolate normally, but FORCE the first point to match the cylinder
            r_end = float(np.interp(x_end, xs, rs))
            mask = (xs > x_start + 1e-5) & (xs < x_end - 1e-5)
            xs_clean = [x_start] + xs[mask].tolist() + [x_end]
            rs_clean = [cyl_radius] + rs[mask].tolist() + [r_end]  # Forced match

        return xs_clean, rs_clean

    @Part(parse=False)
    def revolution_curve(self):
        """1. Draws the top profile line."""
        xs_clean, rs_clean = self.sliced_data
        pts = [(float(x), float(r), 0.0) for x, r in zip(xs_clean, rs_clean)]

        # Use degree 1 for cylinders, degree 3 for curves
        is_cyl = len(pts) == 2
        safe_degree = 1 if is_cyl else min(5, len(pts) - 1)

        return FittedCurve(points=pts, hidden=True, max_degree=safe_degree)

    @Part(parse=False)
    def profile_wire(self):
        """2. Builds a perfectly closed 2D loop."""
        top_edge = self.revolution_curve

        p_start = top_edge.start
        p_end = top_edge.end

        # CHANGED: Central axis math now uses X instead of Z
        axis_end = Point(p_end.x, 0.0, 0.0)
        axis_start = Point(p_start.x, 0.0, 0.0)

        edges = [top_edge]

        # Back Cap (Check Y coordinate for radius)
        if p_end.y > 1e-4:
            edges.append(LineSegment(p_end, axis_end))

        # Bottom Axis Line
        edges.append(LineSegment(axis_end, axis_start))

        # Front Cap
        if p_start.y > 1e-4:
            edges.append(LineSegment(axis_start, p_start))

        return Wire(edges)

    @Part
    def profile_face(self):
        """Fills the closed wire loop to create a solid 2D surface."""
        return Face(island=self.profile_wire, hidden=True)

    @Part
    def solid(self):
        """4. Revolves the filled Face around the X-axis to create a true Solid!"""
        return RevolvedSolid(
            built_from=self.profile_face,
            center=Point(0, 0, 0),
            direction=Vector(1, 0, 0),
            color=self.color if hasattr(self, "color") else "gray",
            transparency=0.8 if self.show_constraints else 0,
            line_thickness=1e-9,
            isos=0
        )

    @Part
    def min_radii(self):
        """List of points (station, radius, 0) in the XY plane."""
        return Circle(quantify=len(self.fuselage_data[0]),
                      radius=self.fuselage_data[2][child.index],
                      position=translate(
                          self.position.rotate90('y'),
                          Vector(1, 0, 0),
                          self.fuselage_data[0][child.index],
                          "x"),
                      color='red',
                      transparency=0 if self.show_constraints else 1
                      )

    @Part
    def max_radii(self):
        """List of points (station, radius, 0) in the XY plane."""
        return Circle(quantify=len(self.fuselage_data[0]),
                      radius=self.fuselage_data[3][child.index],
                      position=translate(
                          self.position.rotate90('y'),
                          Vector(1, 0, 0),
                          self.fuselage_data[0][child.index],
                          "x"),
                      color='red',
                      transparency=0 if self.show_constraints and self.fuselage_data[3][child.index] < 5 else 1,
                      hidden=False if self.fuselage_data[3][child.index] < 5 else True
                      )

    @Attribute
    def error_fuselage(self):
        return self.fuselage_data[5]

    @Attribute
    def fus_length(self):
        return self.fuselage_data[4]


if __name__ == '__main__':
    from parapy.gui import display

    fuselage = Fuselage()
    display(fuselage)