from parapy.geom import GeomBase
from parapy.core import Input, Attribute


class FuselageDataManager(GeomBase):
    """Manages fuselage data and derived attributes."""
    geometry_manager = Input()
    nose_length = Input()
    main_body_length = Input()
    tail_length = Input()
    fuselage_radius = Input()

    user_constraints = Input([])

    @Attribute
    def sections_number(self):
        """Total number of data points across the whole aircraft."""
        return len(self.xs)

    @Attribute
    def length(self):
        return self.nose_length + self.main_body_length + self.tail_length

    @Attribute
    def xs(self):
        """The combined X-stations for the whole aircraft."""
        nose_xs = self.geometry_manager.nose.sliced_data[0]
        # Shift body stations by nose length
        body_xs = [x + self.nose_length for x in self.geometry_manager.main_body.sliced_data[0]]
        # Shift tail stations by nose + body length
        tail_xs = [x + self.nose_length + self.main_body_length for x in self.geometry_manager.tail.sliced_data[0]]
        return nose_xs + body_xs + tail_xs


    @Attribute
    def radii(self):
        """Combined list of fuselage radii at each station."""
        return self.geometry_manager.nose.sliced_data[1] + \
            self.geometry_manager.main_body.sliced_data[1] + \
            self.geometry_manager.tail.sliced_data[1]

    @Attribute
    def min_radii(self):
        radii = [0.0] * self.sections_number
        if not self.user_constraints:
            return radii

        total_length = self.length

        for constraint in self.user_constraints:
            target_x = constraint["x_pct"] * total_length

            # Find the station index closest to this X coordinate
            idx = min(range(self.sections_number), key=lambda i: abs(self.xs[i] - target_x))

            # --- NEW MATH: Calculate the absolute radius based on the local fuselage size ---
            local_fuselage_radius = self.radii[idx]
            target_r = constraint.get("r_pct", 0.5) * local_fuselage_radius

            # Apply to window
            window = 2
            start_idx = max(0, idx - window)
            end_idx = min(self.sections_number, idx + window + 1)

            for i in range(start_idx, end_idx):
                radii[i] = max(radii[i], target_r)

        return radii

    @Attribute
    def max_radii(self):
        """The ceiling constraints for the optimizer (usually current radii)."""
        return self.radii

    @Attribute
    def fus_length(self):
        """Alias for length to satisfy other managers."""
        return self.length