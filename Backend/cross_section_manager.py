import numpy as np
import pandas as pd
from parapy.geom import GeomBase, Plane, Point, Vector
from parapy.geom.future import Common
from parapy.core import Input, Attribute, Part, child


class CrossSectionManager(GeomBase):
    """Manages cross-sectional area calculations with improved smoothing."""
    geometry_manager = Input()
    include_hor_tail = Input()

    fuselage_stations = Input()
    fuselage_radii_list = Input()

    @Attribute
    def fuselage_sections_number(self):
        return len(self.fuselage_stations)

    @Attribute
    def fuselage_length(self):
        return self.fuselage_stations[-1]

    @Attribute
    def fuselage_radii(self):
        return self.fuselage_radii_list

    @Part
    def planes(self):
        return Plane(
            quantify=self.fuselage_sections_number,
            reference=Point(child.index / (self.fuselage_sections_number - 1) * self.fuselage_length, 0, 0),
            normal=Vector(1, 0, 0),
        )

    @Attribute
    def fuselage_cross_sectional_area(self):
        return np.pi * np.array(self.fuselage_radii) ** 2

    @Part
    def wings_cross_sectional_area(self):
        return Common(
            quantify=self.fuselage_sections_number,
            args=[self.planes[child.index]],
            tools=[self.geometry_manager.wings_less_fuselage],
        )

    @Part
    def vert_tail_cross_sections(self):
        return Common(
            quantify=self.fuselage_sections_number,
            args=[self.planes[child.index]],
            tools=[self.geometry_manager.vert_tail_less_fuselage],
        )

    @Part
    def hor_tail_cross_sections(self):
        return Common(
            quantify=self.fuselage_sections_number,
            args=[self.planes[child.index]],
            tools=[self.geometry_manager.hor_tail_less_fuselage if self.include_hor_tail else []],
        )

    def choose_window_by_acf(self, x, threshold=0.05):
        """Improved window selection with dynamic thresholding"""
        x = np.asarray(x) - np.nanmean(x)
        if len(x) < 2:
            return 1

        # Compute autocorrelation function
        corr = np.correlate(x, x, mode="full")
        central_corr = corr[len(x) - 1]

        if central_corr == 0:
            return 3  # Return a safe default window size if data is perfectly flat

        acf = corr[len(x) - 1:] / central_corr

        # Dynamic threshold based on data characteristics
        data_range = np.max(x) - np.min(x)
        std_x = np.std(x)
        dynamic_threshold = max(threshold, 0.1 * (data_range / std_x) if std_x > 0 else threshold)

        # Find first lag below threshold
        below = np.where(acf < dynamic_threshold)[0]
        lag = below[0] if len(below) else max(1, len(x) // 10)

        # Ensure odd window size and minimum size
        win = lag + (lag % 2 == 0)
        return max(3, min(win, len(x) // 2))

    def smooth_component(self, data):
        """Two-stage smoothing with fallback to double moving average"""
        # First pass: moving average
        window_size = self.choose_window_by_acf(data)
        s1 = pd.Series(data).rolling(
            window=window_size,
            min_periods=1,
            center=True
        ).mean().to_numpy()

        # Second pass: smaller window moving average
        window_size2 = max(3, min(window_size // 2, len(data) // 3))
        if window_size2 % 2 == 0:  # Ensure odd window size
            window_size2 = max(3, window_size2 - 1)

        return pd.Series(s1).rolling(
            window=window_size2,
            min_periods=1,
            center=True
        ).mean().to_numpy()

    @Attribute(settable=True)
    def areas(self):
        return []

    @Attribute(settable=True)
    def vert_tail_areas(self):
        return []

    @Attribute(settable=True)
    def hor_tail_areas(self):
        return []

    @Attribute(settable=True)
    def tail_areas(self):
        return []

    @Attribute(settable=True)
    def total(self):
        return []

    @Attribute(settable=True)
    def x(self):
        if len(self.areas) > 1:
            return np.linspace(0, self.fuselage_length, len(self.areas))
        return np.array([0.0])

    def calculate_wings_cross_sectional_area(self):
        area_list = []
        for sec in self.wings_cross_sectional_area:
            try:
                area_list.append(sum(face.area for face in sec.faces[:2]))
            except Exception:
                area_list.append(0.0)

        self.areas = self.smooth_component(area_list)

    def calculate_vert_tail_cross_sectional_area(self):
        vert_list = []
        for sec in self.vert_tail_cross_sections:
            try:
                vert_list.append(sum(face.area for face in sec.faces))
            except Exception:
                vert_list.append(0.0)

        self.vert_tail_areas = self.smooth_component(vert_list)

    def calculate_hor_tail_cross_sectional_area(self):
        hor_list = []
        if self.include_hor_tail:
            for sec in self.hor_tail_cross_sections:
                try:
                    hor_list.append(sum(face.area for face in sec.faces))
                except Exception:
                    hor_list.append(0.0)
        else:
            hor_list = [0.0] * self.fuselage_sections_number

        self.hor_tail_areas = self.smooth_component(hor_list)

    def calculate_tail_cross_sectional_area(self):
        self.calculate_vert_tail_cross_sectional_area()
        self.calculate_hor_tail_cross_sectional_area()
        self.tail_areas = self.vert_tail_areas + self.hor_tail_areas

    def calculate_total_cross_sectional_area(self):
        self.calculate_wings_cross_sectional_area()
        self.calculate_tail_cross_sectional_area()
        fus_areas = self.fuselage_cross_sectional_area
        self.total = self.areas + fus_areas + self.tail_areas