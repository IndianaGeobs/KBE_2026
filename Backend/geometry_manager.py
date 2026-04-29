import sys
import os

# 1. Find the project root directory
current_dir = os.path.dirname(os.path.abspath(__file__))  # Backend folder
parent_dir = os.path.dirname(current_dir)                 # KBE_2026 folder

# 2. Add the project root to Python's search path
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 3. NOW ParaPy and absolute imports will work perfectly!
from parapy.geom import GeomBase, MirroredShape, Subtracted, Compound, Fused
from parapy.core import Input, Part, Attribute

from Backend.lifting_surface import LiftingSurface
from Backend.fuselage import Fuselage
from Readers.fuselage_reader import get_fuselage_data

class GeometryManager(GeomBase):
    """Manages all geometric components of the aircraft."""

    # Inputs
    fuselage_file = Input()
    wing_file = Input()
    vert_tail_file = Input()
    hor_tail_file = Input()
    include_hor_tail = Input()
    show_constraints = Input()

    #Parametric fuselage Inputs
    nose_length = Input(12.6)
    main_body_length = Input(31.5)
    tail_length = Input(18.9)
    fuselage_radius = Input(2.829)

    # Offsets
    x_offs_wings = Input()
    z_offs_wings = Input()
    x_offs_tail = Input()
    z_offs_tail = Input()
    x_offs_vert_tail = Input()
    z_offs_vert_tail = Input()

    '''@Part
    def fuselage(self):
        """Reads station‐&‐radius data from fuselage file."""
        return Fuselage(
            fuselage_file=self.fuselage_file,
            show_constraints=self.show_constraints,
            color="Gray",
        )'''

    @Attribute
    def raw_fuselage_tuple(self):
        """One central place to load the data for all sections."""
        from Readers.fuselage_reader import get_fuselage_data
        return get_fuselage_data(self.fuselage_file)

    @Part
    def nose(self):
        return Fuselage(
            fuselage_data=self.raw_fuselage_tuple,
            position=self.position,
            start_perc=0.0,
            end_perc=0.2,
            color="LightBlue",
            target_length=self.nose_length,
            target_radius=self.fuselage_radius
        )

    @Part
    def main_body(self):
        return Fuselage(
            fuselage_data=self.raw_fuselage_tuple,
            position=self.position.translate('x', self.nose_length),
            start_perc=0.2,
            end_perc=0.7,
            color="Gray",
            target_length=self.main_body_length,
            target_radius=self.fuselage_radius
        )

    @Part
    def tail(self):
        return Fuselage(
            fuselage_data=self.raw_fuselage_tuple,
            position=self.position.translate('x', self.nose_length + self.main_body_length),
            start_perc=0.7,
            end_perc=1.0,
            color="LightSteelBlue",
            target_length=self.tail_length,
            target_radius=self.fuselage_radius
        )

    @Part
    def fuselage_solid(self):
        return Fused(
            shape_in=self.nose.solid,
            tool=[self.main_body.solid, self.tail.solid],
            color="gray",
            line_thickness=1e-9
        )

    @Part
    def right_wing(self):
        return LiftingSurface(
            wing_file=self.wing_file,
            x_offset=self.x_offs_wings,
            z_offset=self.z_offs_wings,
            is_vertical=False,
        )

    @Part
    def left_wing(self):
        return MirroredShape(
            shape_in=self.right_wing.solid,
            reference_point=self.position,
            vector1=self.position.Vz,
            vector2=self.position.Vx,
        )

    @Part
    def wings_pair(self):
        """Compound of left + right wing solids (before subtracting fuselage)."""
        return Compound(built_from=[self.right_wing.solid, self.left_wing])

    @Part
    def wings_less_fuselage(self):
        """Subtract the fuselage from the combined wing pair."""
        return Subtracted(
            shape_in=self.wings_pair,
            tool=self.fuselage_solid,
        )

    @Part
    def vert_tail(self):
        return LiftingSurface(
            wing_file=self.vert_tail_file,
            x_offset=self.x_offs_vert_tail,
            z_offset=self.z_offs_vert_tail,
            is_vertical=True,
        )

    @Part
    def vert_tail_less_fuselage(self):
        """Subtract only the fuselage from the vertical‐tail solid."""
        return Subtracted(
            shape_in=self.vert_tail.solid,
            tool=self.fuselage_solid,
        )

    @Part
    def h_tail_right(self):
        return LiftingSurface(
            wing_file=self.hor_tail_file,
            x_offset=self.x_offs_tail,
            z_offset=self.z_offs_tail,
            is_vertical=False,
            hidden=not self.include_hor_tail,
        )

    @Part
    def h_tail_left(self):
        return MirroredShape(
            shape_in=self.h_tail_right.solid,
            reference_point=self.position,
            vector1=self.position.Vz,
            vector2=self.position.Vx,
            hidden=not self.include_hor_tail,
        )

    @Part
    def hor_tail(self):
        """Fuse right + left horizontal tail into one combined solid first."""
        return Compound(
            built_from=[
                self.h_tail_right.solid,
                self.h_tail_left
            ] if self.include_hor_tail else [],
            transparency=0 if self.include_hor_tail else 1,
            line_thickness=None if self.include_hor_tail else 1e-6
        )

    @Part
    def hor_tail_less_fuselage(self):
        """Subtract only the fuselage from the horizontal‐tail solid."""
        return Subtracted(
            shape_in=self.hor_tail if self.include_hor_tail else [],
            tool=self.fuselage_solid,
        )

    @Part
    def aircraft_solid(self):
        """The full combined aircraft."""
        return Compound(
            built_from=[
                self.fuselage_solid,  # This is the Fused nose/body/tail
                self.wings_pair,
                self.vert_tail.solid,
                *([self.hor_tail] if self.include_hor_tail else [])
            ],
            color="gray",
            line_thickness=0
        )