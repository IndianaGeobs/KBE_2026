from parapy.core import Base, Input, Attribute, Part
from parapy.geom.future import Common

class OptimizedIntersectionChecker(Base):
    """
    Manages intersection checks specifically for the optimized aircraft configuration.
    """

    # Input parameters - lifting surface components
    right_wing    = Input()
    h_tail_right  = Input()
    vert_tail     = Input()
    new_fuselage  = Input()  # The optimized fuselage from OptimizedResults

    # Offset parameters for dependency tracking
    x_offs_wings      = Input()
    z_offs_wings      = Input()
    x_offs_tail       = Input()
    z_offs_tail       = Input()
    x_offs_vert_tail  = Input()
    z_offs_vert_tail  = Input()

    @Part
    def inters_right_wing_fuselage_root_curve_new(self):
        return Common(
            args=[self.right_wing.airfoil_curves[0]],
            tools=[self.new_fuselage.solid],
        )

    @Part
    def inters_right_hor_tail_fuselage_root_curve_new(self):
        return Common(
            args=[self.h_tail_right.airfoil_curves[0]],
            tools=[self.new_fuselage.solid],
        )

    @Part
    def inters_vert_tail_fuselage_root_curve_new(self):
        return Common(
            args=[self.vert_tail.airfoil_curves[0]],
            tools=[self.new_fuselage.solid],
        )

    @Attribute
    def wing_fuselage_check_new(self):
        vertices = self.inters_right_wing_fuselage_root_curve_new.vertices
        is_error = len(vertices) != 1
        self.error_lifting_surface_wing_new = is_error
        return is_error

    @Attribute
    def wing_fuselage_intersection_new_status(self):
        _ = (self.x_offs_wings, self.z_offs_wings)
        return self.wing_fuselage_check_new

    @Attribute
    def hor_tail_fuselage_check_new(self):
        vertices_ht = self.inters_right_hor_tail_fuselage_root_curve_new.vertices
        is_error = len(vertices_ht) != 1
        self.error_lifting_surface_ht_new = is_error
        return is_error

    @Attribute
    def hor_tail_fuselage_intersection_new_status(self):
        _ = (self.x_offs_tail, self.z_offs_tail)
        return self.hor_tail_fuselage_check_new

    @Attribute
    def vert_tail_fuselage_check_new(self):
        vertices_vt = self.inters_vert_tail_fuselage_root_curve_new.vertices
        is_error = len(vertices_vt) != 1
        self.error_lifting_surface_vt_new = is_error
        return is_error

    @Attribute
    def vert_tail_fuselage_intersection_new_status(self):
        _ = (self.x_offs_vert_tail, self.z_offs_vert_tail)
        return self.vert_tail_fuselage_check_new

    @Attribute
    def has_optimized_intersection_errors(self):
        return any([
            self.wing_fuselage_intersection_new_status,
            self.hor_tail_fuselage_intersection_new_status,
            self.vert_tail_fuselage_intersection_new_status,
        ])

    @Attribute
    def optimized_overall_error_status(self):
        return self.has_optimized_intersection_errors

    def get_optimized_error_summary(self):
        return {
            'optimized_intersection_errors': {
                'wing_fuselage_new': self.wing_fuselage_intersection_new_status,
                'hor_tail_fuselage_new': self.hor_tail_fuselage_intersection_new_status,
                'vert_tail_fuselage_new': self.vert_tail_fuselage_intersection_new_status,
            },
            'optimized_overall_status': self.optimized_overall_error_status,
        }

    def get_intersection_comparison(self):
        return {
            'wing_fuselage': {
                'optimized': self.wing_fuselage_intersection_new_status,
                'intersection_count': len(self.inters_right_wing_fuselage_root_curve_new.vertices),
            },
            'hor_tail_fuselage': {
                'optimized': self.hor_tail_fuselage_intersection_new_status,
                'intersection_count': len(self.inters_right_hor_tail_fuselage_root_curve_new.vertices),
            },
            'vert_tail_fuselage': {
                'optimized': self.vert_tail_fuselage_intersection_new_status,
                'intersection_count': len(self.inters_vert_tail_fuselage_root_curve_new.vertices),
            },
        }