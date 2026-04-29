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
    def zs(self):
        """The combined Z-elevations (camber) for the whole aircraft."""
        try:
            # Grab the 3rd index [2] from the sliced data
            nose_zs = self.geometry_manager.nose.sliced_data[2]
            body_zs = self.geometry_manager.main_body.sliced_data[2]
            tail_zs = self.geometry_manager.tail.sliced_data[2]

            # Just glue the lists together (no length addition needed for vertical Z)
            return nose_zs + body_zs + tail_zs

        except IndexError:
            # FAILSAFE: If your parser was strictly written to only keep [0] and [1]
            # and it threw away the Z data, this prevents a crash and defaults to 0.0
            return [0.0] * len(self.xs)

    @Attribute
    def radii(self):
        """Combined list of fuselage radii at each station."""
        return self.geometry_manager.nose.sliced_data[1] + \
               self.geometry_manager.main_body.sliced_data[1]

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