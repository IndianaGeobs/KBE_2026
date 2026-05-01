
# ------------------- OUTDATED BY PARAMETRIC_WING -------------------- #



import os
import sys

# --- PATH FIXES ---
# Get the directory of the current script (the 'Backend' folder)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the main project folder ('KBE_2026')
parent_dir = os.path.dirname(current_dir)
# Add the main folder to Python's map so it can find the 'Readers' package
sys.path.append(parent_dir)

# Create an absolute path to your default file in the 'Files' folder
DEFAULT_WING_PATH = os.path.join(parent_dir, "Files", "wing.txt")

from Readers.lifting_surface_reader import get_wing_data
from parapy.core import Part, Input, Attribute, child
from parapy.geom import GeomBase, Point, FittedCurve, LoftedSolid

class LiftingSurface(GeomBase):
    """
    Loads wing-station DAT files, applies chord & twist, and creates one
    FittedCurve per station, then lofts them into a solid.
    """
    # Use the absolute path calculated above as the default
    wing_file = Input(DEFAULT_WING_PATH)
    x_offset = Input(1.0)
    z_offset = Input(1.0)
    is_vertical = Input(False)

    @Attribute
    def points(self):
        """Processes raw data into ParaPy Point objects with offsets."""
        data = get_wing_data(self.wing_file)
        station_pts = data[0]

        out = []
        for pts in station_pts:
            station_list = []
            for x0, y0, z0 in pts:
                # Handle vertical rotation (e.g., for Vertical Tail)
                if self.is_vertical:
                    x1, y1, z1 = x0, -z0, y0
                else:
                    x1, y1, z1 = x0, y0, z0

                # apply offsets:
                station_list.append(
                    Point(x1 + self.x_offset,
                          y1,
                          z1 + self.z_offset)
                )
            out.append(station_list)
        return out

    @Part
    def airfoil_curves(self):
        """One FittedCurve per station. First statement is 'return' for ParaPy parser."""
        return FittedCurve(
            quantify=get_wing_data(self.wing_file)[1],
            points=self.points[child.index],
            tolerance=0.01
        )

    @Part
    def solid(self):
        """Lofts the curves into a B-Rep solid."""
        return LoftedSolid(
            profiles=self.airfoil_curves,
            ruled=True
        )

    @Attribute
    def error_lifting_surface(self):
        """Returns the error flag from the reader."""
        return get_wing_data(self.wing_file)[2]

if __name__ == '__main__':
    from parapy.gui import display

    lifting_surface = LiftingSurface()
    display(lifting_surface)