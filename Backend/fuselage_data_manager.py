from parapy.geom import GeomBase
from parapy.core import Input, Attribute


class FuselageDataManager(GeomBase):
    """Manages fuselage data and derived attributes."""
    geometry_manager = Input()
    nose_length = Input()
    main_body_length = Input()
    tail_length = Input()
    fuselage_radius = Input()

    @Attribute
    def sections_number(self):
        # We access the first element of the tuple returned by sliced_data
        return len(self.geometry_manager.nose.sliced_data[0])

    @Attribute
    def length(self):
        return self.nose_length + self.main_body_length + self.tail_length

    @Attribute
    def xs(self):
        """The combined X-stations for the whole aircraft."""
        # sliced_data[0] is the X list, sliced_data[1] is the R list
        nose_xs = self.geometry_manager.nose.sliced_data[0]
        body_xs = [x + self.nose_length for x in self.geometry_manager.main_body.sliced_data[0]]
        tail_xs = [x + self.nose_length + self.main_body_length for x in self.geometry_manager.tail.sliced_data[0]]
        return nose_xs + body_xs + tail_xs

    @Attribute
    def radii(self):
        """Combined list of fuselage radii at each station."""
        return self.geometry_manager.nose.sliced_data[1] + \
               self.geometry_manager.main_body.sliced_data[1]

    @Attribute
    def min_radii(self):
        """The floor constraints for the optimizer."""
        # If your Fuselage class has a min_radius attribute, use that.
        # Otherwise, we can return a list of zeros or a safe minimum.
        return [0.0] * self.sections_number

    @Attribute
    def max_radii(self):
        """The ceiling constraints for the optimizer (usually current radii)."""
        return self.radii

    @Attribute
    def fus_length(self):
        """Alias for length to satisfy other managers."""
        return self.length