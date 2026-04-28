import os
from parapy.core import Base, Input, Part
from Backend.aircraft import Aircraft

# --- PATH LOGIC ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
FILES_DIR = os.path.join(parent_dir, "Files")

# Use the exact same DEF variables as Aircraft
DEF_FUS = os.path.join(FILES_DIR, "fuselage.json")  # Corrected to JSON
DEF_WING = os.path.join(FILES_DIR, "wing_default.txt")
DEF_VT = os.path.join(FILES_DIR, "vert_tail_default.txt")
DEF_HT = os.path.join(FILES_DIR, "hor_tail_default.txt")


class AreaRule(Base):
    """AreaRule: live aircraft parameters"""
    # UPDATE THESE INPUTS:
    fuselage_file = Input(DEF_FUS)
    wing_file = Input(DEF_WING)
    vert_tail_file = Input(DEF_VT)
    hor_tail_file = Input(DEF_HT)

    include_hor_tail = Input(True)

    x_offs_wings = Input(20)
    z_offs_wings = Input(-2)
    x_offs_tail = Input(54.0)
    z_offs_tail = Input(0.0)
    x_offs_vert_tail = Input(53.0)
    z_offs_vert_tail = Input(0.0)
    show_constraints = Input(False)

    @Part
    def aircraft(self):
        return Aircraft(
            fuselage_file=self.fuselage_file,
            wing_file=self.wing_file,
            vert_tail_file=self.vert_tail_file,
            hor_tail_file=self.hor_tail_file,
            include_hor_tail=self.include_hor_tail,
            x_offs_wings=self.x_offs_wings,
            z_offs_wings=self.z_offs_wings,
            x_offs_tail=self.x_offs_tail,
            z_offs_tail=self.z_offs_tail,
            x_offs_vert_tail=self.x_offs_vert_tail,
            z_offs_vert_tail=self.z_offs_vert_tail,
            show_constraints=self.show_constraints,
        )


# Global instance shared across the web app components
AR = AreaRule()