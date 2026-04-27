import matplotlib.pyplot as plt
from parapy.geom import GeomBase
from parapy.core import Input

class GraphManager(GeomBase):
    """Manages all plotting and visualization functionality."""
    cross_sections = Input()  # Reference to CrossSectionManager
    optimization = Input()  # Reference to OptimizationManager

    def graph_wings_cross_sectional_area(self):
        self.cross_sections.calculate_wings_cross_sectional_area()
        fig = plt.figure(figsize=(10, 5))
        plt.plot(self.cross_sections.x, self.cross_sections.areas, "-", label="Wings")
        plt.xlabel("Fuselage axis position (m)")
        plt.ylabel("Area (m²)")
        plt.title("Wing Cross‐Sectional Area")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        return fig

    def graph_tail_cross_sectional_area(self):
        """Single combined tail curve (vertical + horizontal)."""
        self.cross_sections.calculate_tail_cross_sectional_area()
        fig = plt.figure(figsize=(10, 5))
        plt.plot(self.cross_sections.x, self.cross_sections.tail_areas, "-", label="Tail")
        plt.xlabel("Fuselage axis position (m)")
        plt.ylabel("Area (m²)")
        plt.title("Tail Cross‐Sectional Area")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        return fig

    def graph_total_cross_sectional_area(self):
        self.cross_sections.calculate_total_cross_sectional_area()
        fig = plt.figure(figsize=(10, 5))
        plt.plot(self.cross_sections.x, self.cross_sections.total, "-", label="Total")
        plt.xlabel("Position (m)")
        plt.ylabel("Area (m²)")
        plt.title("Combined Cross‐Sectional Area (Fuselage + Wing + Tail)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        return fig

    def graph_init_opt_fus_cross_sect_area(self):
        """Plot fuselage A_f(z) for initial vs. optimized."""
        xmin, xmax = self.cross_sections.x.min(), self.cross_sections.x.max()
        ymin = min(self.optimization.Af_0_sq.min(), self.optimization.Af_opt_sq.min())
        ymax = max(self.optimization.Af_0_sq.max(), self.optimization.Af_opt_sq.max(),
                   self.optimization.tot_in_sq.min(), self.optimization.tot_in_sq.max(),
                   self.optimization.tot_opt_sq.min(), self.optimization.tot_opt_sq.max())

        fig = plt.figure(figsize=(10, 5))
        plt.plot(self.cross_sections.x, self.optimization.Af_0_sq, "k-", label="Initial fuselage")
        plt.plot(self.cross_sections.x, self.optimization.Af_opt_sq,
                 color="deepskyblue", linestyle="-", label="Optimized fuselage")
        plt.xlabel("Station z (m)")
        plt.ylabel("Fuselage Area A_f(z) (m²)")
        plt.title("Fuselage Area Distribution: Initial vs. Optimized")
        plt.grid(True)
        plt.legend()
        plt.xlim(xmin, xmax)
        plt.ylim(ymin, ymax)
        plt.tight_layout()
        return fig

    def graph_init_opt_tot_cross_sect_area(self):
        """Plot total A_total(z) for initial vs. optimized."""
        self.optimization.call_optimizator()

        xmin, xmax = self.cross_sections.x.min(), self.cross_sections.x.max()
        ymin = min(self.optimization.Af_0_sq.min(), self.optimization.Af_opt_sq.min(),
                   self.optimization.tot_in_sq.min(), self.optimization.tot_opt_sq.min())
        ymax = max(self.optimization.Af_0_sq.max(), self.optimization.Af_opt_sq.max(),
                   self.optimization.tot_in_sq.max(), self.optimization.tot_opt_sq.max())

        fig = plt.figure(figsize=(10, 5))
        plt.plot(self.cross_sections.x, self.optimization.tot_in_sq, "k-", label="Initial total")
        plt.plot(self.cross_sections.x, self.optimization.tot_opt_sq,
                 color="deepskyblue", linestyle="-", label="Optimized total")
        plt.xlabel("Station z (m)")
        plt.ylabel("Total Area A_total(z) (m²)")
        plt.title("Total Area Distribution: Initial vs. Optimized")
        plt.grid(True)
        plt.legend()
        plt.xlim(xmin, xmax)
        plt.ylim(ymin, ymax)
        plt.tight_layout()
        return fig

    def twod_graph_init_opt_fuselage(self, base_width=20):
        """2D contour (top) of initial vs. optimized fuselage."""
        x_limits = (self.optimization.Zc.min(), self.optimization.Zc.max())
        y_limits = (
            min(self.optimization.X0.min(), self.optimization.Xopt.min()),
            max(self.optimization.X0.max(), self.optimization.Xopt.max()),
        )
        span_z = x_limits[1] - x_limits[0]
        span_x = y_limits[1] - y_limits[0]
        padding_z_left = span_z * 0.07
        padding_z_right = span_z * 0.01
        padding_x = span_x * 0.1

        fig_height = base_width * (span_x / span_z)
        fig, ax = plt.subplots(figsize=(base_width, fig_height))

        ax.contourf(
            self.optimization.Zc, self.optimization.X0, self.optimization.Y0,
            levels=[self.optimization.Y0.min(), 0], colors=["gray"], alpha=0.5,
        )
        ax.contour(
            self.optimization.Zc, self.optimization.X0, self.optimization.Y0,
            levels=[0], colors="black", linewidths=2,
        )

        ax.contourf(
            self.optimization.Zc, self.optimization.Xopt, self.optimization.Yopt,
            levels=[self.optimization.Yopt.min(), 0], colors=["skyblue"], alpha=0.5,
        )
        ax.contour(
            self.optimization.Zc, self.optimization.Xopt, self.optimization.Yopt,
            levels=[0], colors="deepskyblue", linewidths=2,
        )

        ax.set_xlim(x_limits[0] - padding_z_left, x_limits[1] + padding_z_right)
        ax.set_ylim(y_limits[0] - padding_x, y_limits[1] + padding_x)
        ax.set_aspect("equal")
        ax.set_xlabel("Z (m)")
        ax.set_ylabel("X (m)")
        ax.set_title("Original vs. Optimized Fuselages (Top View)")

        ax.plot([], [], color="black", label="Original", linewidth=2)
        ax.plot([], [], color="deepskyblue", label="Optimized", linewidth=2)
        ax.legend(bbox_to_anchor=(0.1, 0.5), loc="center right", fontsize="small")

        plt.tight_layout()
        return fig