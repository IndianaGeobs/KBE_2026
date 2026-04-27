from parapy.geom import GeomBase, MirroredShape, Subtracted, Compound
from parapy.core import Input, Part

from lifting_surface import LiftingSurface
from fuselage import Fuselage

class GeometryManager(GeomBase):
    """Manages all geometric components of the aircraft."""

    # Inputs
    fuselage_file = Input()
    wing_file = Input()
    vert_tail_file = Input()
    hor_tail_file = Input()
    include_hor_tail = Input()
    show_constraints = Input()

    # Offsets
    x_offs_wings = Input()
    z_offs_wings = Input()
    x_offs_tail = Input()
    z_offs_tail = Input()
    x_offs_vert_tail = Input()
    z_offs_vert_tail = Input()

    @Part
    def fuselage(self):
        """Reads station‐&‐radius data from `fuselage_file`."""
        return Fuselage(
            fuselage_file=self.fuselage_file,
            show_constraints=self.show_constraints,
            color="Gray",
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
            tool=self.fuselage.solid,
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
            tool=self.fuselage.solid,
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
            tool=self.fuselage.solid,
        )

    @Part
    def aircraft_solid(self):
        """The full combined aircraft (fuselage fused with wings & tail)."""
        return Compound(
            built_from=[
                self.fuselage.solid,
                self.wings_pair,
                self.vert_tail.solid,
                *(
                    [self.hor_tail]
                    if self.include_hor_tail
                    else []
                )
            ],
            color="gray"
        )