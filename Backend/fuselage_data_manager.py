from parapy.geom import GeomBase
from parapy.core import Input, Attribute

class FuselageDataManager(GeomBase):
    """Manages fuselage data and derived attributes."""
    geometry_manager = Input()  # Reference to GeometryManager instance

    @Attribute
    def sections_number(self):
        """Number of fuselage sections."""
        return len(self.geometry_manager.fuselage.revolution_curve.points)

    @Attribute
    def length(self):
        """Total length of fuselage."""
        return self.geometry_manager.fuselage.revolution_curve.points[-1][2]

    @Attribute
    def radii(self):
        """List of fuselage radii at each station."""
        return [pt[1] for pt in self.geometry_manager.fuselage.revolution_curve.points]

    @Attribute
    def min_radii(self):
        """Minimum radius constraints along fuselage."""
        return [r.radius for r in self.geometry_manager.fuselage.min_radii]

    @Attribute
    def max_radii(self):
        """Maximum radius constraints along fuselage."""
        return [r.radius for r in self.geometry_manager.fuselage.max_radii]

    @Attribute
    def fuselage_length(self):
        """Returns the fuselage's length."""
        return self.geometry_manager.fuselage.fus_length