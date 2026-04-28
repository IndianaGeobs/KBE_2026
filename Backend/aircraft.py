import os
from parapy.geom import GeomBase
from parapy.core import Input, Part, action, Attribute

# 1. BUILD THE ABSOLUTE PATHS HERE
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
FILES_DIR = os.path.join(parent_dir, "Files")

# 2. DEFINE THE CORRECT FILENAMES
DEF_FUS = os.path.join(FILES_DIR, "fuselage.json") # Note: .json
DEF_WING = os.path.join(FILES_DIR, "wing_default.txt")
DEF_VT = os.path.join(FILES_DIR, "vert_tail_default.txt")
DEF_HT = os.path.join(FILES_DIR, "hor_tail_default.txt")

# Local module imports
from Backend.fuselage_data_manager import FuselageDataManager
from Backend.geometry_manager import GeometryManager
from Backend.intersection_manager import IntersectionManager
from Backend.cross_section_manager import CrossSectionManager
from Backend.optimization_manager import OptimizationManager
from Backend.graph_manager import GraphManager
from Backend.optimized_results import OptimizedResults
from Backend.intersection_checker import IntersectionChecker
from Backend.optimized_intersection_checker import OptimizedIntersectionChecker


class Aircraft(GeomBase):
    """Main Aircraft class that orchestrates all managers."""

    fuselage_file = Input(DEF_FUS)
    wing_file = Input(DEF_WING)
    vert_tail_file = Input(DEF_VT)
    hor_tail_file = Input(DEF_HT)

    include_hor_tail = Input(True)
    show_constraints = Input(False)

    # Offsets
    x_offs_wings = Input(20)
    z_offs_wings = Input(0.0)
    x_offs_tail = Input(55)
    z_offs_tail = Input(0.0)
    x_offs_vert_tail = Input(55)
    z_offs_vert_tail = Input(0.0)

    @Part
    def geometry(self):
        """Manages all geometric components."""
        return GeometryManager(
            # Pass the absolute paths down to the GeometryManager
            fuselage_file=self.fuselage_file,
            wing_file=self.wing_file,
            vert_tail_file=self.vert_tail_file,
            hor_tail_file=self.hor_tail_file,
            include_hor_tail=self.include_hor_tail,
            show_constraints=self.show_constraints,
            x_offs_wings=self.x_offs_wings,
            z_offs_wings=self.z_offs_wings,
            x_offs_tail=self.x_offs_tail,
            z_offs_tail=self.z_offs_tail,
            x_offs_vert_tail=self.x_offs_vert_tail,
            z_offs_vert_tail=self.z_offs_vert_tail,
        )


    @Part
    def fuselage_data(self):
        return FuselageDataManager(geometry_manager=self.geometry)

    @Part
    def intersections(self):
        return IntersectionManager(geometry_manager=self.geometry)

    @Part
    def cross_sections(self):
        return CrossSectionManager(
            geometry_manager=self.geometry,
            include_hor_tail=self.include_hor_tail,
        )

    @Part
    def optimization(self):
        """Manages MATLAB optimization calculations."""
        return OptimizationManager(
            cross_sections=self.cross_sections,
            fuselage_data=self.fuselage_data,
        )

    @Part
    def graphs(self):
        """Manages all plotting and visualization."""
        return GraphManager(
            cross_sections=self.cross_sections,
            optimization=self.optimization,
        )

    @Part
    def intersection_checker(self):
        """Manages all intersection checks and error detection."""
        return IntersectionChecker(
            inters_right_wing_fuselage_root_curve=self.intersections.inters_right_wing_fuselage_root_curve,
            inters_right_hor_tail_fuselage_root_curve=self.intersections.inters_right_hor_tail_fuselage_root_curve,
            inters_vert_tail_fuselage_root_curve=self.intersections.inters_vert_tail_fuselage_root_curve,
            inters_hor_tail_wing=self.intersections.inters_hor_tail_wing,
            inters_vert_tail_wings=self.intersections.inters_vert_tail_wings,
            inters_vert_tail_hor_tail=self.intersections.inters_vert_tail_hor_tail,
            wings_first_cross_sectional_area=self.cross_sections.wings_cross_sectional_area[0] if self.cross_sections.wings_cross_sectional_area else None,
            wings_last_cross_sectional_area=self.cross_sections.wings_cross_sectional_area[-1] if self.cross_sections.wings_cross_sectional_area else None,
            ht_first_cross_sectional_area=self.cross_sections.hor_tail_cross_sections[0] if self.cross_sections.hor_tail_cross_sections else None,
            ht_last_cross_sectional_area=self.cross_sections.hor_tail_cross_sections[-1] if self.cross_sections.hor_tail_cross_sections else None,
            vt_first_cross_sectional_area=self.cross_sections.vert_tail_cross_sections[0] if self.cross_sections.vert_tail_cross_sections else None,
            vt_last_cross_sectional_area=self.cross_sections.vert_tail_cross_sections[-1] if self.cross_sections.vert_tail_cross_sections else None,
            x_offs_wings=self.x_offs_wings,
            z_offs_wings=self.z_offs_wings,
            x_offs_tail=self.x_offs_tail,
            z_offs_tail=self.z_offs_tail,
            x_offs_vert_tail=self.x_offs_vert_tail,
            z_offs_vert_tail=self.z_offs_vert_tail,
            fuselage_file=self.fuselage_file,
            wing_file=self.wing_file,
            fuselage=self.geometry.fuselage,
            right_wing=self.geometry.right_wing,
        )

    @Part
    def optimized_results(self):
        """Handles optimized fuselage results and exports."""
        return OptimizedResults(
            fuselage=self.geometry.fuselage,
            r_optimized=self.optimization.r_optimized,
            fuselage_min_radii=self.fuselage_data.min_radii,
            fuselage_max_radii=self.fuselage_data.max_radii,
            wings_pair=self.geometry.wings_pair,
            vert_tail=self.geometry.vert_tail,
            hor_tail=self.geometry.hor_tail if self.include_hor_tail else None,
            include_hor_tail=self.include_hor_tail,
        )

    @Part
    def optimized_intersection_checker(self):
        """Manages intersection checks for optimized aircraft configuration."""
        return OptimizedIntersectionChecker(
            right_wing=self.geometry.right_wing,
            h_tail_right=self.geometry.h_tail_right,
            vert_tail=self.geometry.vert_tail,
            new_fuselage=self.optimized_results.new_fuselage,
            x_offs_wings=self.x_offs_wings,
            z_offs_wings=self.z_offs_wings,
            x_offs_tail=self.x_offs_tail,
            z_offs_tail=self.z_offs_tail,
            x_offs_vert_tail=self.x_offs_vert_tail,
            z_offs_vert_tail=self.z_offs_vert_tail,
        )

    @action(label="Optimize & Show All Plots")
    def show_all_plots(self):
        figs = []
        figs.append(self.graphs.graph_init_opt_tot_cross_sect_area())
        figs.append(self.graphs.graph_init_opt_fus_cross_sect_area())
        figs.append(self.graphs.twod_graph_init_opt_fuselage())
        return figs

    @action(label="Check All Intersections")
    def check_all_intersections(self):
        original_errors = self.intersection_checker.get_error_summary()
        optimized_errors = self.optimized_intersection_checker.get_optimized_error_summary()
        return {
            'original_configuration': original_errors,
            'optimized_configuration': optimized_errors,
            'comparison': self.optimized_intersection_checker.get_intersection_comparison()
        }

    @action(label="Export All Optimized Results")
    def export_all_optimized(self):
        self.optimized_results.download_optimized_fuselage_data()
        self.optimized_results.step_file_optimized_fuselage()
        self.optimized_results.step_file_optimized_aircraft()

    # Convenience properties
    @Attribute
    def fuselage(self):
        return self.geometry.fuselage_solid

    @property
    def right_wing(self):
        return self.geometry.right_wing

    @property
    def left_wing(self):
        return self.geometry.left_wing

    @property
    def wings_pair(self):
        return self.geometry.wings_pair

    @property
    def wings_less_fuselage(self):
        return self.geometry.wings_less_fuselage

    @property
    def vert_tail(self):
        return self.geometry.vert_tail

    @property
    def vert_tail_less_fuselage(self):
        return self.geometry.vert_tail_less_fuselage

    @property
    def h_tail_right(self):
        return self.geometry.h_tail_right

    @property
    def h_tail_left(self):
        return self.geometry.h_tail_left

    @property
    def hor_tail(self):
        return self.geometry.hor_tail

    @property
    def hor_tail_less_fuselage(self):
        return self.geometry.hor_tail_less_fuselage

    @property
    def aircraft_solid(self):
        return self.geometry.aircraft_solid

    @property
    def optimized_fuselage(self):
        return self.optimized_results.new_fuselage

    @property
    def optimized_aircraft_solid(self):
        return self.optimized_results.optimized_aircraft

    @property
    def has_errors(self):
        return self.intersection_checker.overall_error_status

    @property
    def has_optimized_errors(self):
        return self.optimized_intersection_checker.optimized_overall_error_status