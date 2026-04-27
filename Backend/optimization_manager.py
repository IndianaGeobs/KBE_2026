import numpy as np
from parapy.geom import GeomBase
from parapy.core import Input, Attribute


class OptimizationManager(GeomBase):
    """Manages MATLAB optimization and related calculations."""
    cross_sections = Input()  # Reference to CrossSectionManager
    fuselage_data = Input()  # Reference to FuselageDataManager

    # Optimization results
    @Attribute(settable=True)
    def Af_0_sq(self):
        return []

    @Attribute(settable=True)
    def Af_opt_sq(self):
        return []

    @Attribute(settable=True)
    def tot_in_sq(self):
        return []

    @Attribute(settable=True)
    def tot_opt_sq(self):
        return []

    @Attribute(settable=True)
    def r_initial(self):
        return []

    @Attribute(settable=True)
    def r_optimized(self):
        return []

    @Attribute(settable=True)
    def theta(self):
        return []

    @Attribute(settable=True)
    def Zc(self):
        return []

    @Attribute(settable=True)
    def X0(self):
        return []

    @Attribute(settable=True)
    def Y0(self):
        return []

    @Attribute(settable=True)
    def Xopt(self):
        return []

    @Attribute(settable=True)
    def Yopt(self):
        return []

    # Scalar optimization metrics
    @Attribute(settable=True)
    def rough_X0(self):
        return 0.0

    @Attribute(settable=True)
    def rough_opt(self):
        return 0.0

    @Attribute(settable=True)
    def rough_reduction(self):
        return 0.0

    @Attribute(settable=True)
    def A_ext_0(self):
        return 0.0

    @Attribute(settable=True)
    def A_ext_opt(self):
        return 0.0

    @Attribute(settable=True)
    def ext_area_change(self):
        return 0.0

    def call_optimizator(self):
        """
        Calls MATLAB optimizer with cross-sectional data.
        """
        # 1) Compute all cross-section arrays
        self.cross_sections.calculate_total_cross_sectional_area()
        self.cross_sections.calculate_wings_cross_sectional_area()
        self.cross_sections.calculate_tail_cross_sectional_area()

        # 2) Pack MATLAB inputs
        import matlab.engine
        eng = matlab.engine.start_matlab()

        z_ml = matlab.double(self.cross_sections.x.tolist())
        wing_ml = matlab.double(self.cross_sections.areas.tolist())
        tail_ml = matlab.double(self.cross_sections.tail_areas.tolist())
        fus_ml = matlab.double(self.cross_sections.fuselage_cross_sectional_area.tolist())
        min_ml = matlab.double(self.fuselage_data.min_radii)

        # 3) Call fuselage_optimizer
        outputs = eng.fuselage_optimizer(
            z_ml, wing_ml, tail_ml, fus_ml, min_ml, nargout=10
        )

        # 4) Assign outputs
        tot_in = outputs[0]
        tot_opt = outputs[1]
        r_initial_ml = outputs[2]
        r_optimized_ml = outputs[3]
        self.A_ext_0 = outputs[4]
        self.A_ext_opt = outputs[5]
        self.rough_X0 = outputs[6]
        self.rough_opt = outputs[7]
        Af_0 = outputs[8]
        Af_opt = outputs[9]

        # Flatten to numpy arrays
        self.Af_0_sq = np.squeeze(Af_0)
        self.Af_opt_sq = np.squeeze(Af_opt)
        self.tot_in_sq = np.squeeze(tot_in)
        self.tot_opt_sq = np.squeeze(tot_opt)
        self.r_initial = np.squeeze(r_initial_ml)
        self.r_optimized = np.squeeze(r_optimized_ml)

        # Roughness reduction ratio
        if self.rough_X0 != 0:
            self.rough_reduction = float((self.rough_opt - self.rough_X0) / self.rough_X0 * 100)
        else:
            self.rough_reduction = 0.0

        # Build the 2D & 3D arrays for plotting
        n_theta = 100
        self.theta = np.linspace(0, 2 * np.pi, n_theta)
        self.Zc = np.tile(self.cross_sections.x, (n_theta, 1)).T

        # X0, Y0 (initial fuselage)
        self.X0 = np.outer(self.r_initial, np.cos(self.theta)) + 3 * np.max(self.r_initial)
        self.Y0 = np.outer(self.r_initial, np.sin(self.theta))

        # Xopt, Yopt (optimized fuselage)
        self.Xopt = np.outer(self.r_optimized, np.cos(self.theta))
        self.Yopt = np.outer(self.r_optimized, np.sin(self.theta))

        # External area change
        if self.A_ext_0 != 0:
            self.ext_area_change = float((self.A_ext_opt - self.A_ext_0) / self.A_ext_0 * 100)
        else:
            self.ext_area_change = 0.0