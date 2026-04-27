import os
import numpy as np
from math import radians

from parapy.core import Part, Attribute, Input, child
from parapy.geom import GeomBase, Point, FittedCurve, Revolution, RotatedShape, Vector, Circle, translate

# Import the read_fuselage function from your module
from fuselage_reader import get_fuselage_data

class Fuselage(GeomBase):
    """
    ParaPy GeomBase for creating a fuselage by revolving a radial profile
    loaded from a text file.
    """
    fuselage_file = Input('fuselage.txt')
    show_constraints = Input(False)
    error_reading_fuselage = Input(False)
    max_revolution_curve_degree = Input(8)

    @Attribute
    def fuselage_data(self):
        """
        Reads the fuselage file and returns x-stations, radii, constraints, and length.
        """
        return get_fuselage_data(self.fuselage_file)

    @Part
    def revolution_curve(self):
        return FittedCurve(points= [(0.0, r, x) for x, r in zip(self.fuselage_data[0], self.fuselage_data[1])], hidden = True, max_degree = self.max_revolution_curve_degree)

    @Part
    def solid(self):
        # rotate so that fuselage axis aligns with X or Y as needed
        return RotatedShape(
            shape_in= Revolution(curve_in=self.revolution_curve),
            rotation_point=Point(0, 0, 0),
            vector=Vector(0, 1, 0),
            angle=radians(90),
            transparency = 0.8 if self.show_constraints else 0,
            line_thickness = 1e-6,
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
                      color = 'red',
                      transparency = 0 if self.show_constraints else 1
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
                      hidden = False if self.fuselage_data[3][child.index] < 5 else True
                      )

    @Attribute
    def error_fuselage(self):
        return self.fuselage_data[5]

    @Attribute
    def fus_length(self):
        return self.fuselage_data[4]

if __name__ == '__main__':
    from parapy.gui import display

    # Example usage: supply path to your fuselage.txt
    fuselage = Fuselage()
    display(fuselage)
