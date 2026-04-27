from parapy.core import Base, Input, Part
from aircraft import Aircraft  # Updated from your newly split backend files


class AreaRule(Base):
    """AreaRule: live aircraft parameters"""
    fuselage_file = Input("fuselage_default.txt")
    wing_file = Input("wing_default.txt")
    vert_tail_file = Input("vert_tail_default.txt")
    hor_tail_file = Input("hor_tail_default.txt")
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