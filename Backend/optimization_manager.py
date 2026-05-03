import numpy as np
from scipy.optimize import minimize, Bounds
from parapy.core import Base, Input, Attribute


class OptimizationManager(Base):
    """Manages SciPy optimization and related calculations using Analytical Jacobian."""
    cross_sections = Input()  # Reference to CrossSectionManager
    fuselage_data = Input()  # Reference to FuselageDataManager

    # Optimization results
    @Attribute(settable=True)
    def Af_0_sq(self): return []

    @Attribute(settable=True)
    def Af_opt_sq(self): return []

    @Attribute(settable=True)
    def tot_in_sq(self): return []

    @Attribute(settable=True)
    def tot_opt_sq(self): return []

    @Attribute(settable=True)
    def r_initial(self): return []

    @Attribute(settable=True)
    def r_optimized(self): return []

    @Attribute(settable=True)
    def theta(self): return []

    @Attribute(settable=True)
    def Zc(self): return []

    @Attribute(settable=True)
    def X0(self): return []

    @Attribute(settable=True)
    def Y0(self): return []

    @Attribute(settable=True)
    def Xopt(self): return []

    @Attribute(settable=True)
    def Yopt(self): return []

    # Scalar optimization metrics
    @Attribute(settable=True)
    def rough_X0(self): return 0.0

    @Attribute(settable=True)
    def rough_opt(self): return 0.0

    @Attribute(settable=True)
    def rough_reduction(self): return 0.0

    @Attribute(settable=True)
    def A_ext_0(self): return 0.0

    @Attribute(settable=True)
    def A_ext_opt(self): return 0.0

    @Attribute(settable=True)
    def ext_area_change(self): return 0.0

    @Attribute(settable=True)
    def Vf_0(self): return 0.0

    @Attribute(settable=True)
    def Vf_opt(self): return 0.0

    @Attribute(settable=True)
    def volume_change(self): return 0.0

    def call_optimizator(self):
        """Calls SciPy optimizer with cross-sectional data and Analytical Jacobian."""
        # 1) Compute all cross-section arrays
        self.cross_sections.calculate_total_cross_sectional_area()
        self.cross_sections.calculate_wings_cross_sectional_area()
        self.cross_sections.calculate_tail_cross_sectional_area()

        # 2) Extract arrays
        z = np.asarray(self.cross_sections.x)
        A_wing = np.asarray(self.cross_sections.areas)
        A_tail = np.asarray(self.cross_sections.tail_areas)
        Af0 = np.asarray(self.cross_sections.fuselage_cross_sectional_area)
        r0 = np.sqrt(Af0 / np.pi)
        r_min_raw = np.asarray(self.fuselage_data.min_radii)
        r_max = np.asarray(self.fuselage_data.max_radii)
        r_min = np.maximum(r_min_raw, r0 * 0.30)


        n = len(z)

        # Integration weights (trapezoidal rule)
        dz = np.diff(z)
        w = np.zeros(n)
        w[0] = dz[0] / 2
        w[-1] = dz[-1] / 2
        w[1:-1] = (dz[:-1] + dz[1:]) / 2

        self.Vf_0 = np.sum(w * Af0)

        # Bounds
        bounds = Bounds(lb=np.pi * (r_min ** 2), ub=np.pi * (r_max ** 2))

        # Build the Second-Difference Matrix (D)
        D = np.zeros((n - 2, n))
        for i in range(n - 2):
            D[i, i] = 1.0
            D[i, i + 1] = -2.0
            D[i, i + 2] = 1.0

        # Objective Function
        def total_obj(Af):
            return np.sum(np.diff(Af + A_wing + A_tail, n=2) ** 2)

        # Analytical Gradient (Jacobian)
        def total_obj_jac(Af):
            Atot = Af + A_wing + A_tail
            E = np.diff(Atot, n=2)
            return 2.0 * (D.T @ E)

        options = {'maxiter': 10000, 'ftol': 1e-9, 'disp': True}

        # 3) Run Optimization
        res = minimize(
            total_obj,
            x0=Af0,
            method='SLSQP',
            bounds=bounds,
            jac=total_obj_jac,
            options=options
        )

        # 4) Assign outputs
        Af_opt = res.x
        self.rough_opt = res.fun
        self.rough_X0 = total_obj(Af0)

        self.tot_in_sq = Af0 + A_wing + A_tail
        self.tot_opt_sq = Af_opt + A_wing + A_tail
        self.Af_0_sq = Af0
        self.Af_opt_sq = Af_opt

        self.Vf_opt = np.sum(w * Af_opt)

        r = np.sqrt(Af0 / np.pi)
        r_opt = np.sqrt(Af_opt / np.pi)
        self.r_initial = r
        self.r_optimized = r_opt

        # Skin surface calculations
        drdz0 = np.gradient(r, z)
        drdz_opt = np.gradient(r_opt, z)

        integrand0 = 2 * np.pi * r * np.sqrt(1 + drdz0 ** 2)
        integrand_opt = 2 * np.pi * r_opt * np.sqrt(1 + drdz_opt ** 2)

        self.A_ext_0 = np.trapezoid(integrand0, x=z)
        self.A_ext_opt = np.trapezoid(integrand_opt, x=z)

        # Deltas
        self.rough_reduction = float(
            (self.rough_opt - self.rough_X0) / self.rough_X0 * 100) if self.rough_X0 != 0 else 0.0
        self.ext_area_change = float((self.A_ext_opt - self.A_ext_0) / self.A_ext_0 * 100) if self.A_ext_0 != 0 else 0.0
        self.volume_change = float((self.Vf_opt - self.Vf_0) / self.Vf_0 * 100) if self.Vf_0 != 0 else 0.0

        # Contours setup for 2D UI Graphing
        n_theta = 100
        self.theta = np.linspace(0, 2 * np.pi, n_theta)
        self.Zc = np.tile(z, (n_theta, 1)).T
        self.X0 = np.outer(self.r_initial, np.cos(self.theta)) + 3 * np.max(self.r_initial)
        self.Y0 = np.outer(self.r_initial, np.sin(self.theta))
        self.Xopt = np.outer(self.r_optimized, np.cos(self.theta))
        self.Yopt = np.outer(self.r_optimized, np.sin(self.theta))