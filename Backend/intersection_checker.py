from parapy.core import Base, Input, Attribute

import os


class IntersectionChecker(Base):
    """Manages all intersection checks and error detection for aircraft components."""

    # Input geometry objects
    inters_right_wing_fuselage_root_curve = Input()
    inters_right_hor_tail_fuselage_root_curve = Input()
    inters_vert_tail_fuselage_root_curve = Input()
    inters_hor_tail_wing = Input()
    inters_vert_tail_wings = Input()
    inters_vert_tail_hor_tail = Input()

    # Cross-sectional area objects for tip checking
    wings_first_cross_sectional_area = Input()
    wings_last_cross_sectional_area = Input()
    ht_first_cross_sectional_area = Input()
    ht_last_cross_sectional_area = Input()
    vt_first_cross_sectional_area = Input()
    vt_last_cross_sectional_area = Input()

    # Offset parameters for dependency tracking
    x_offs_wings = Input()
    z_offs_wings = Input()
    x_offs_tail = Input()
    z_offs_tail = Input()
    x_offs_vert_tail = Input()
    z_offs_vert_tail = Input()

    # File reading inputs
    fuselage_file = Input()
    wing_file = Input()
    fuselage = Input()
    right_wing = Input()

    @Attribute
    def wing_fuselage_check(self):
        vertices = self.inters_right_wing_fuselage_root_curve.vertices
        is_error = len(vertices) != 1
        self.error_lifting_surface = is_error
        return is_error

    @Attribute
    def wing_fuselage_intersection_status(self):
        _ = (self.x_offs_wings, self.z_offs_wings)
        return self.wing_fuselage_check

    @Attribute
    def hor_tail_fuselage_check(self):
        vertices_ht = self.inters_right_hor_tail_fuselage_root_curve.vertices
        is_error_ht = len(vertices_ht) != 1
        self.error_lifting_surface = is_error_ht
        return is_error_ht

    @Attribute
    def hor_tail_fuselage_intersection_status(self):
        _ = (self.x_offs_tail, self.z_offs_tail)
        return self.hor_tail_fuselage_check

    @Attribute
    def vert_tail_fuselage_check(self):
        vertices_vt = self.inters_vert_tail_fuselage_root_curve.vertices
        is_error_vt = len(vertices_vt) != 1
        self.error_lifting_surface = is_error_vt
        return is_error_vt

    @Attribute
    def vert_tail_fuselage_intersection_status(self):
        _ = (self.x_offs_vert_tail, self.z_offs_vert_tail)
        return self.vert_tail_fuselage_check

    @Attribute
    def wing_hor_tail_check(self):
        wires_wht = self.inters_hor_tail_wing.wires
        is_error_wht = len(wires_wht) != 0
        self.error_lifting_surface = is_error_wht
        return is_error_wht

    @Attribute
    def wing_hor_tail_intersection_status(self):
        _ = (self.x_offs_tail, self.z_offs_tail, self.x_offs_wings, self.z_offs_wings)
        return self.wing_hor_tail_check

    @Attribute
    def wing_vert_tail_intersection_check(self):
        wires_wvt = self.inters_vert_tail_wings.wires
        is_error_wvt = len(wires_wvt) != 0
        self.error_wings_vert_tail_inter = is_error_wvt
        return is_error_wvt

    @Attribute
    def wing_vert_tail_intersection_status(self):
        _ = (self.x_offs_vert_tail, self.z_offs_vert_tail, self.x_offs_wings, self.z_offs_wings)
        return self.wing_vert_tail_intersection_check

    @Attribute
    def hor_tail_vert_tail_intersection_check(self):
        wires_htvt = self.inters_vert_tail_hor_tail.wires
        is_error_htvt = len(wires_htvt) != 0
        self.error_hor_tail_vert_tail_inter = is_error_htvt
        return is_error_htvt

    @Attribute
    def hor_tail_vert_tail_intersection_status(self):
        _ = (self.x_offs_vert_tail, self.z_offs_vert_tail, self.x_offs_tail, self.z_offs_tail)
        return self.hor_tail_vert_tail_intersection_check

    @Attribute
    def wing_tip_out_fus_check(self):
        is_error_tip_wing = (len(self.wings_first_cross_sectional_area.vertices) != 0 or
                             len(self.wings_last_cross_sectional_area.vertices) != 0)
        self.error_wing_tip = is_error_tip_wing
        return is_error_tip_wing

    @Attribute
    def wing_tip_out_fus_status(self):
        _ = (self.x_offs_wings, self.z_offs_wings)
        return self.wing_tip_out_fus_check

    @Attribute
    def hor_tail_tip_out_fus_check(self):
        is_error_tip_ht = (len(self.ht_first_cross_sectional_area.vertices) != 0 or
                           len(self.ht_last_cross_sectional_area.vertices) != 0)
        self.error_ht_tip = is_error_tip_ht
        return is_error_tip_ht

    @Attribute
    def hor_tail_tip_out_fus_status(self):
        _ = (self.x_offs_tail, self.z_offs_tail)
        return self.hor_tail_tip_out_fus_check

    @Attribute
    def vert_tail_tip_out_fus_check(self):
        is_error_tip_vt = (len(self.vt_first_cross_sectional_area.vertices) != 0 or
                           len(self.vt_last_cross_sectional_area.vertices) != 0)
        self.error_vt_tip = is_error_tip_vt
        return is_error_tip_vt

    @Attribute
    def vert_tip_out_fus_status(self):
        _ = (self.x_offs_vert_tail, self.z_offs_vert_tail)
        return self.vert_tail_tip_out_fus_check

    @Attribute
    def fuselage_reading_error_status(self):
        _ = self.fuselage_file
        if not self.fuselage_file or not os.path.exists(self.fuselage_file):
            return True
        return False

    @Attribute
    def lifting_surface_reading_error_status(self):
        _ = self.wing_file
        return self.right_wing.error_lifting_surface

    @Attribute
    def has_intersection_errors(self):
        return any([
            self.wing_fuselage_intersection_status, self.hor_tail_fuselage_intersection_status,
            self.vert_tail_fuselage_intersection_status, self.wing_hor_tail_intersection_status,
            self.wing_vert_tail_intersection_status, self.hor_tail_vert_tail_intersection_status,
        ])

    @Attribute
    def has_tip_errors(self):
        return any([
            self.wing_tip_out_fus_status, self.hor_tail_tip_out_fus_status, self.vert_tip_out_fus_status,
        ])

    @Attribute
    def has_file_errors(self):
        return any([
            self.fuselage_reading_error_status, self.lifting_surface_reading_error_status,
        ])

    @Attribute
    def overall_error_status(self):
        return self.has_intersection_errors or self.has_tip_errors or self.has_file_errors

    def get_error_summary(self):
        return {
            'intersection_errors': {
                'wing_fuselage': self.wing_fuselage_intersection_status,
                'hor_tail_fuselage': self.hor_tail_fuselage_intersection_status,
                'vert_tail_fuselage': self.vert_tail_fuselage_intersection_status,
                'wing_hor_tail': self.wing_hor_tail_intersection_status,
                'wing_vert_tail': self.wing_vert_tail_intersection_status,
                'hor_tail_vert_tail': self.hor_tail_vert_tail_intersection_status,
            },
            'tip_errors': {
                'wing_tip': self.wing_tip_out_fus_status,
                'hor_tail_tip': self.hor_tail_tip_out_fus_status,
                'vert_tail_tip': self.vert_tip_out_fus_status,
            },
            'file_errors': {
                'fuselage_reading': self.fuselage_reading_error_status,
                'lifting_surface_reading': self.lifting_surface_reading_error_status,
            },
            'overall_status': self.overall_error_status,
        }