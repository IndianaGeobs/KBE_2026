import os
import sys
import numpy as np

# Get the directory of the current script (the 'Backend' folder)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from Readers.fuselage_reader import get_fuselage_data

DEFAULT_FUSELAGE = os.path.join(parent_dir, "Files", "fuselage.json")

from parapy.core import Part, Attribute, Input
from parapy.geom import GeomBase, Point, Circle, LoftedSolid


class Fuselage(GeomBase):
    """
    Creates a fuselage section using Lofting.
    The Main Body is a perfect cylinder. The Tail has a flat top and curves upward.
    """

    target_length = Input(15.0)
    target_radius = Input(2.8)

    start_perc = Input(0.0)
    end_perc = Input(1.0)
    fuselage_data = Input()
    fuselage_file = Input(DEFAULT_FUSELAGE)
    show_constraints = Input(False)

    # Give color an explicit default so it doesn't crash if omitted
    color = Input("gray")

    @Attribute
    def sliced_data(self):
        xs, rs, min_r, max_r, length, err = self.fuselage_data

        x_start = self.start_perc * length
        x_end = self.end_perc * length

        # Identify which section we are currently building
        is_nose = self.start_perc < 0.05
        is_tail = self.end_perc > 0.95
        is_main_body = not is_nose and not is_tail

        # Calculate exact mating radius at the 20% mark
        nose_end_x = 0.2 * length
        cyl_radius = float(np.interp(nose_end_x, xs, rs))

        if is_main_body:
            # Force perfect cylinder using the nose's exit radius
            xs_clean = [x_start, x_end]
            rs_clean = [cyl_radius, cyl_radius]

        elif is_nose:
            # Nose naturally ends at nose_end_x. Force the final point to match.
            r_start = float(np.interp(x_start, xs, rs))
            mask = (xs > x_start + 1e-5) & (xs < x_end - 1e-5)
            xs_clean = [x_start] + xs[mask].tolist() + [x_end]
            rs_clean = [r_start] + rs[mask].tolist() + [cyl_radius]

        elif is_tail:
            # The tail starts at 70%. We force its very first radius to
            # match the cylinder to prevent a shelf/step.
            r_end = float(np.interp(x_end, xs, rs))
            mask = (xs > x_start + 1e-5) & (xs < x_end - 1e-5)
            xs_clean = [x_start] + xs[mask].tolist() + [x_end]
            rs_clean = [cyl_radius] + rs[mask].tolist() + [r_end]

        original_section_length = xs_clean[-1] - xs_clean[0]

        scaled_xs = []
        for x in xs_clean:
            new_x = ((x - xs_clean[0])/original_section_length)*self.target_length
            scaled_xs.append(new_x)

        original_max_radius = self.target_radius
        scaled_rs = [(r/original_max_radius)*self.target_radius for r in rs_clean]

        return scaled_xs, scaled_rs

    @Part(parse=False)
    def cross_sections(self):
        """Generates the circular ribs to stretch the skin over."""
        xs_clean, rs_clean = self.sliced_data

        # We need the cylinder radius to know where our "Flat Top" ceiling is
        length = self.fuselage_data[4]
        cyl_radius = float(np.interp(0.2 * length, self.fuselage_data[0], self.fuselage_data[1]))

        is_tail = self.end_perc > 0.95

        ribs = []
        for x, r in zip(xs_clean, rs_clean):
            # THE ZERO-RADIUS FIX:
            # If the radius is literally 0.0, we make it 0.1 millimeters instead.
            # This is completely invisible, but it prevents the CAD math from crashing!
            safe_r = max(float(r), 1e-4)

            # THE FLAT TOP MATH:
            # Normally, the top of a circle is at Y = +safe_r.
            # We want the top to stay perfectly flush with the ceiling (+cyl_radius).
            # To do that, we shift the center of the circle UP by the difference.
            if is_tail:
                z_shift = cyl_radius - safe_r
            else:
                z_shift = 0.0

            # Position the circle: Move to X, move UP to Y, and rotate 90 deg around Y
            # so the circle faces down the X-axis (standing up instead of lying flat).
            pos = self.position.translate('x', float(x)).translate('z', z_shift).rotate90('y')

            ribs.append(Circle(radius=safe_r, position=pos, hidden=True))

        return ribs

    @Part(parse=False)
    def solid(self):
        """Wraps a perfectly sealed 3D solid skin over the circular ribs."""
        return LoftedSolid(
            profiles=self.cross_sections,
            ruled=True,
            color=self.color,
            line_thickness=1e-9,  # Micro-value to bypass validation error
            isos=0,  # Hides the web lines across the surface
            transparency=0.8 if self.show_constraints else 0
        )


if __name__ == '__main__':
    from parapy.gui import display

    display(Fuselage())