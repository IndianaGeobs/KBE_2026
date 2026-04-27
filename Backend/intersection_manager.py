from parapy.geom import GeomBase
from parapy.geom.future import Common
from parapy.core import Input, Part

class IntersectionManager(GeomBase):
    """Manages all intersection operations between aircraft components."""
    geometry_manager = Input()  # Reference to GeometryManager instance

    @Part
    def inters_right_wing_fuselage_root_curve(self):
        return Common(
            args=[self.geometry_manager.right_wing.airfoil_curves[0]],
            tools=[self.geometry_manager.fuselage.solid],
        )

    @Part
    def inters_right_hor_tail_fuselage_root_curve(self):
        return Common(
            args=[self.geometry_manager.h_tail_right.airfoil_curves[0]],
            tools=[self.geometry_manager.fuselage.solid],
        )

    @Part
    def inters_vert_tail_fuselage_root_curve(self):
        return Common(
            args=[self.geometry_manager.vert_tail.airfoil_curves[0]],
            tools=[self.geometry_manager.fuselage.solid],
        )

    @Part
    def inters_hor_tail_wing(self):
        return Common(
            args=[self.geometry_manager.wings_less_fuselage],
            tools=[self.geometry_manager.hor_tail_less_fuselage],
        )

    @Part
    def inters_vert_tail_wings(self):
        return Common(
            args=[self.geometry_manager.wings_less_fuselage],
            tools=[self.geometry_manager.vert_tail_less_fuselage],
        )

    @Part
    def inters_vert_tail_hor_tail(self):
        return Common(
            args=[self.geometry_manager.hor_tail_less_fuselage],
            tools=[self.geometry_manager.vert_tail_less_fuselage],
        )