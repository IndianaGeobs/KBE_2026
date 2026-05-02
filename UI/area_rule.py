import os
from parapy.core import Base, Input, Part, Attribute
from Backend.aircraft import Aircraft
from parapy.geom import Compound, Circle, Position, Point, Vector, YOZ
from Backend.geometry_manager import GeometryManager

# --- PATH LOGIC ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
FILES_DIR = os.path.join(parent_dir, "Files")

# Use the exact same DEF variables as Aircraft
DEF_FUS = os.path.join(FILES_DIR, "fuselage.json")  # Corrected to JSON
DEF_WING = os.path.join(FILES_DIR, "trial_airfoil_dense.txt")
DEF_VT = os.path.join(FILES_DIR, "vert_tail_dense.txt")
DEF_HT = os.path.join(FILES_DIR, "hor_tail_dense.txt")


class AreaRule(Base):
    """AreaRule: live aircraft parameters"""
    fuselage_file = Input(DEF_FUS)
    wing_file = Input(DEF_WING)
    vert_tail_file = Input(DEF_VT)
    hor_tail_file = Input(DEF_HT)

    include_hor_tail = Input(True)

    x_offs_wings = Input(0.35)
    z_offs_wings = Input(0.0)
    x_offs_tail = Input(0.8)
    z_offs_tail = Input(0.2)
    x_offs_vert_tail = Input(0.8)
    z_offs_vert_tail = Input(0.0)
    show_constraints = Input(False)

    wing_dihedral = Input(5.0)
    wing_root_chord_ratio = Input(0.2)
    wing_sections_ratios = Input([{"span": 0.40, "root_chord": 0.2, "tip_chord": 0.05, "sweep": 25.0}])

    vt_root_chord_ratio = Input(0.08)
    vt_span_ratio = Input(0.11)
    vt_tip_chord_ratio = Input(0.03)
    vt_sweep = Input(43.0)

    ht_root_chord_ratio = Input(0.08)
    ht_span_ratio = Input(0.11)
    ht_tip_chord_ratio = Input(0.03)
    ht_sweep = Input(43.0)

    nose_length = Input(12.6)
    main_body_length = Input(31.5)
    tail_length = Input(18.9)
    fuselage_radius = Input(2.829)

    user_constraints = Input([])

    @Part(parse=False)
    def aircraft(self):
        total = self.nose_length + self.main_body_length + self.tail_length
        return Aircraft(
            fuselage_file=self.fuselage_file,
            wing_file=self.wing_file,
            vert_tail_file=self.vert_tail_file,
            hor_tail_file=self.hor_tail_file,
            include_hor_tail=self.include_hor_tail,
            x_offs_wings=self.x_offs_wings * total,
            z_offs_wings=self.z_offs_wings * self.fuselage_radius,
            x_offs_tail=self.x_offs_tail * total,
            z_offs_tail=self.z_offs_tail * self.fuselage_radius,
            x_offs_vert_tail=self.x_offs_vert_tail * total,
            z_offs_vert_tail=self.z_offs_vert_tail * self.fuselage_radius,
            wing_dihedral=self.wing_dihedral,
            wing_root_chord=self.actual_wing_root_chord,
            wing_sections=self.actual_wing_sections,
            vt_root_chord=self.actual_vt_root_chord,
            vt_sections=self.actual_vt_sections,
            ht_root_chord=self.actual_ht_root_chord,
            ht_sections=self.actual_ht_sections,
            show_constraints=self.show_constraints,
            nose_length=self.nose_length,
            main_body_length=self.main_body_length,
            tail_length=self.tail_length,
            fuselage_radius=self.fuselage_radius,
            user_constraints=self.user_constraints
        )

    @Attribute
    def total_fuselage_length(self):
        """Helper to get the full length of the plane."""
        return self.nose_length + self.main_body_length + self.tail_length

    @Attribute
    def actual_wing_root_chord(self):
        """Converts the ratio back into physical meters."""
        return self.wing_root_chord_ratio * self.total_fuselage_length

    @Attribute
    def actual_wing_sections(self):
        """Converts all section ratios back into physical meters."""
        sections_in_meters = []
        for sec in self.wing_sections_ratios:
            sections_in_meters.append({
                # Keep keys as 'span' and 'tip_chord' to match the UI dictionary!
                "span": sec["span"] * self.total_fuselage_length,
                "tip_chord": sec["tip_chord"] * self.total_fuselage_length,
                "sweep": sec["sweep"]  # Angles don't scale
            })
        return sections_in_meters

    @Attribute
    def actual_vt_root_chord(self):
        return self.vt_root_chord_ratio * self.total_fuselage_length

    @Attribute
    def actual_vt_sections(self):
        return [{"span": self.vt_span_ratio * self.total_fuselage_length,
                 "tip_chord": self.vt_tip_chord_ratio * self.total_fuselage_length,
                 "sweep": self.vt_sweep}]

    @Attribute
    def actual_ht_root_chord(self):
        return self.ht_root_chord_ratio * self.total_fuselage_length

    @Attribute
    def actual_ht_sections(self):
        return [{"span": self.ht_span_ratio * self.total_fuselage_length,
                 "tip_chord": self.ht_tip_chord_ratio * self.total_fuselage_length,
                 "sweep": self.ht_sweep}]

    @Attribute
    def is_fuselage_modified(self):
        try:
            return (self.fuselage_file != AR.fuselage_file or
                    self.nose_length != AR.nose_length or
                    self.main_body_length != AR.main_body_length or
                    self.tail_length != AR.tail_length or
                    self.fuselage_radius != AR.fuselage_radius)
        except NameError:
            return False

    @Attribute
    def are_wings_modified(self):
        try:
            return (self.wing_file != AR.wing_file or
                    self.x_offs_wings != AR.x_offs_wings or
                    self.z_offs_wings != AR.z_offs_wings or
                    self.wing_dihedral != AR.wing_dihedral or
                    self.wing_root_chord_ratio != AR.wing_root_chord_ratio or
                    self.wing_sections_ratios != AR.wing_sections_ratios)
        except NameError:
            return False

    @Attribute
    def is_vt_modified(self):
        try:
            return (self.vert_tail_file != AR.vert_tail_file or
                    self.x_offs_vert_tail != AR.x_offs_vert_tail or
                    self.z_offs_vert_tail != AR.z_offs_vert_tail or
                    self.vt_root_chord_ratio != AR.vt_root_chord_ratio or
                    self.vt_span_ratio != AR.vt_span_ratio or
                    self.vt_tip_chord_ratio != AR.vt_tip_chord_ratio or
                    self.vt_sweep != AR.vt_sweep)
        except NameError:
            return False

    @Attribute
    def is_ht_modified(self):
        try:
            return (self.include_hor_tail != AR.include_hor_tail or
                    self.hor_tail_file != AR.hor_tail_file or
                    self.x_offs_tail != AR.x_offs_tail or
                    self.z_offs_tail != AR.z_offs_tail or
                    self.ht_root_chord_ratio != AR.ht_root_chord_ratio or
                    self.ht_span_ratio != AR.ht_span_ratio or
                    self.ht_tip_chord_ratio != AR.ht_tip_chord_ratio or
                    self.ht_sweep != AR.ht_sweep)
        except NameError:
            return False

    @Part
    def ghost_geometry_manager(self):
        """A lightweight geometry manager that natively tracks live slider movements."""
        return GeometryManager(
            fuselage_file=self.fuselage_file,
            wing_file=self.wing_file,
            vert_tail_file=self.vert_tail_file,
            hor_tail_file=self.hor_tail_file,
            include_hor_tail=self.include_hor_tail,
            show_constraints=self.show_constraints,

            # Use self.nose_length (the CAD input), which sync_ghost updates in real-time
            x_offs_wings=self.x_offs_wings * (self.nose_length + self.main_body_length + self.tail_length),
            z_offs_wings=self.z_offs_wings * self.fuselage_radius,

            x_offs_tail=self.x_offs_tail * (self.nose_length + self.main_body_length + self.tail_length),
            z_offs_tail=self.z_offs_tail * self.fuselage_radius,

            x_offs_vert_tail=self.x_offs_vert_tail * (self.nose_length + self.main_body_length + self.tail_length),
            z_offs_vert_tail=self.z_offs_vert_tail * self.fuselage_radius,

            wing_dihedral=self.wing_dihedral,
            wing_root_chord=self.actual_wing_root_chord,
            wing_sections=self.actual_wing_sections,
            vt_root_chord=self.actual_vt_root_chord,
            vt_sections=self.actual_vt_sections,
            ht_root_chord=self.actual_ht_root_chord,
            ht_sections=self.actual_ht_sections,
            nose_length=self.nose_length,
            main_body_length=self.main_body_length,
            tail_length=self.tail_length,
            fuselage_radius=self.fuselage_radius
        )

    @Part
    def ghost_fuselage(self):
        return Compound(
            built_from=[
                self.ghost_geometry_manager.nose.solid,
                self.ghost_geometry_manager.main_body.solid,
                self.ghost_geometry_manager.tail.solid
            ] if self.is_fuselage_modified else [],
            color="cyan",
            transparency=0.8,
            line_thickness=1e-9,
            hidden=not self.is_fuselage_modified
        )

    @Part
    def ghost_wings(self):
        return Compound(
            # We use the raw right/left wings here so they don't accidentally inherit the yellow color from wings_pair
            built_from=[
                self.ghost_geometry_manager.right_wing.solid,
                self.ghost_geometry_manager.left_wing
            ] if self.are_wings_modified else [],
            color="cyan",
            transparency=0.5,
            line_thickness=1e-9,
            hidden=not self.are_wings_modified
        )

    @Part
    def ghost_vt(self):
        return Compound(
            built_from=[self.ghost_geometry_manager.vert_tail.solid] if self.is_vt_modified else [],
            color="cyan",
            transparency=0.5,
            line_thickness=1e-9,
            hidden=not self.is_vt_modified
        )

    @Part
    def ghost_ht(self):
        return Compound(
            built_from=[self.ghost_geometry_manager.hor_tail] if (
                        self.include_hor_tail and self.is_ht_modified) else [],
            color="cyan",
            transparency=0.5,
            line_thickness=1e-9,
            hidden=not (self.include_hor_tail and self.is_ht_modified)
        )

    @Part(parse=False)
    def ghost_constraints(self):
        """Draws fast wireframe circles for the ghost constraints, properly centered on the local fuselage."""

        n_len = self.nose_length
        b_len = self.main_body_length
        t_len = self.tail_length
        f_rad = self.fuselage_radius

        ghost_total_length = n_len + b_len + t_len
        tail_start_pct = (n_len + b_len) / ghost_total_length

        try:
            xs = self.aircraft.fuselage_data.xs
            radii = self.aircraft.fuselage_data.radii
        except AttributeError:
            xs = []
            radii = []

        def get_true_fuselage_radius(x_pct):
            """Finds the actual physical radius of the fuselage at this X position."""
            target_x = x_pct * ghost_total_length
            safe_len = min(len(xs), len(radii))

            if safe_len == 0:
                return f_rad

            idx = min(range(safe_len), key=lambda i: abs(xs[i] - target_x))
            return radii[idx]

        circles = []
        for c in self.user_constraints:
            x_pct = c["x_pct"]
            r_pct = c.get("r_pct", 0.5)

            # 1. Get the TRUE radius of the fuselage at this section
            true_fuse_radius = get_true_fuselage_radius(x_pct)

            if true_fuse_radius <= 0:
                continue

            # 2. Calculate the constraint's radius based on the percentage
            constraint_radius = true_fuse_radius * r_pct

            # 3. Find the Y-center of the fuselage using the Flat Top rule
            # Notice we use `true_fuse_radius` here, NOT the constraint radius!
            if x_pct > tail_start_pct:
                y_center = f_rad - true_fuse_radius
            else:
                y_center = 0.0

            # 4. Create the wireframe circle centered exactly at y_center
            circles.append(
                Circle(
                    radius=constraint_radius,
                    position=YOZ.translate("z", x_pct * ghost_total_length).translate("y", y_center)
                )
            )

        return Compound(
            built_from=circles,
            color="red",
            line_thickness=3,
            display_mode="wireframe",
            hidden=not self.show_constraints
        )


# Global instances shared across the web app components
AR = AreaRule()
PREVIEW_AR = AreaRule()