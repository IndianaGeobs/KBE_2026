import os
from parapy.core import Base, Input, Part
from Backend.aircraft import Aircraft

# --- PATH LOGIC ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
FILES_DIR = os.path.join(parent_dir, "Files")

# Use the exact same DEF variables as Aircraft
DEF_FUS = os.path.join(FILES_DIR, "fuselage.json")  # Corrected to JSON
DEF_WING = os.path.join(FILES_DIR, "trial_airfoil.txt")
DEF_VT = os.path.join(FILES_DIR, "vert_tail_default.txt")
DEF_HT = os.path.join(FILES_DIR, "hor_tail_default.txt")


class AreaRule(Base):
    """AreaRule: live aircraft parameters"""
    fuselage_file = Input(DEF_FUS)
    wing_file = Input(DEF_WING)
    vert_tail_file = Input(DEF_VT)
    hor_tail_file = Input(DEF_HT)

    include_hor_tail = Input(True)

    x_offs_wings = Input(0.35)
    z_offs_wings = Input(0.0)
    x_offs_tail = Input(0.75)
    z_offs_tail = Input(0.0)
    x_offs_vert_tail = Input(0.75)
    z_offs_vert_tail = Input(0.0)
    show_constraints = Input(False)

    wing_dihedral = Input(5.0)
    wing_root_chord = Input(4.5)
    wing_sections = Input([{"span": 8.0, "tip_chord": 1.5, "sweep": 25.0}])

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
            show_constraints=self.show_constraints,
            nose_length=self.nose_length,
            main_body_length=self.main_body_length,
            tail_length=self.tail_length,
            fuselage_radius=self.fuselage_radius,
            user_constraints = self.user_constraints,
            wing_dihedral=self.wing_dihedral,
            wing_root_chord=self.wing_root_chord,
            wing_sections=self.wing_sections
        )


# Global instance shared across the web app components
AR = AreaRule()