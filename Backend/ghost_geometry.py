import sys
import os

# 1. Find the project root directory so we can import from UI
current_dir = os.path.dirname(os.path.abspath(__file__))  # Backend folder
parent_dir = os.path.dirname(current_dir)                 # KBE_2026 folder
ui_dir = os.path.join(parent_dir, "UI")                   # UI folder

if ui_dir not in sys.path:
    sys.path.insert(0, ui_dir)

from parapy.geom import Compound, GeomBase
from parapy.core import Part, Attribute

# Import PREVIEW_AR from the UI folder!
from UI.area_rule import PREVIEW_AR
from Backend.geometry_manager import GeometryManager


class GhostGeometry(GeomBase):
    """Creates a fast, uncut, transparent cyan hologram by tracking slider dependencies directly."""

    @Attribute
    def total_length(self):
        """Standard attribute calculation to keep @Part grammar strictly one-line."""
        return PREVIEW_AR.nose_length + PREVIEW_AR.main_body_length + PREVIEW_AR.tail_length

    @Part
    def geometry(self):
        """Builds a lightweight geometry manager that tracks the live PREVIEW sliders perfectly."""
        return GeometryManager(
            fuselage_file=PREVIEW_AR.fuselage_file,
            wing_file=PREVIEW_AR.wing_file,
            vert_tail_file=PREVIEW_AR.vert_tail_file,
            hor_tail_file=PREVIEW_AR.hor_tail_file,
            include_hor_tail=PREVIEW_AR.include_hor_tail,
            show_constraints=PREVIEW_AR.show_constraints,
            x_offs_wings=PREVIEW_AR.x_offs_wings * self.total_length,
            z_offs_wings=PREVIEW_AR.z_offs_wings * PREVIEW_AR.fuselage_radius,
            x_offs_tail=PREVIEW_AR.x_offs_tail * self.total_length,
            z_offs_tail=PREVIEW_AR.z_offs_tail * PREVIEW_AR.fuselage_radius,
            x_offs_vert_tail=PREVIEW_AR.x_offs_vert_tail * self.total_length,
            z_offs_vert_tail=PREVIEW_AR.z_offs_vert_tail * PREVIEW_AR.fuselage_radius,
            nose_length=PREVIEW_AR.nose_length,
            main_body_length=PREVIEW_AR.main_body_length,
            tail_length=PREVIEW_AR.tail_length,
            fuselage_radius=PREVIEW_AR.fuselage_radius,
            wing_dihedral=PREVIEW_AR.wing_dihedral,
            wing_root_chord=PREVIEW_AR.actual_wing_root_chord,
            wing_sections=PREVIEW_AR.actual_wing_sections,
            vt_root_chord=PREVIEW_AR.actual_vt_root_chord,
            vt_sections=PREVIEW_AR.actual_vt_sections,
            ht_root_chord=PREVIEW_AR.actual_ht_root_chord,
            ht_sections=PREVIEW_AR.actual_ht_sections
        )

    @Part
    def wings(self):
        return Compound(
            built_from=[self.geometry.wings_pair],
            color="cyan",
            transparency=0.6
        )

    @Part
    def vt(self):
        return Compound(
            built_from=[self.geometry.vert_tail.solid],
            color="cyan",
            transparency=0.6
        )

    @Part
    def ht(self):
        # Inlined the list generation to adhere to strict 1-line @Part parsing
        return Compound(
            built_from=[self.geometry.hor_tail] if PREVIEW_AR.include_hor_tail else [],
            color="cyan",
            transparency=0.6 if PREVIEW_AR.include_hor_tail else 1.0
        )

# Instantiate the global hologram generator
GHOST = GhostGeometry()