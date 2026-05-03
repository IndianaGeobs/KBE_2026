import os
import shutil
import numpy as np
from parapy.core import Base, Input, Attribute, Part, action
from parapy.geom import Compound, GeomBase, Circle, LoftedSolid
from parapy.exchange.step import STEPWriter

class OptimizedFuselage(GeomBase):
    """Builds a continuous 3D loft directly from the optimizer's raw data arrays."""
    xs = Input()
    rs = Input()
    color = Input("deepskyblue")

    @Part(parse=False)
    def cross_sections(self):
        ribs = []
        for x, r in zip(self.xs, self.rs):
            # Safe minimum radius to prevent CAD engine crashes
            safe_r = max(float(r), 1e-4)
            # Position the circle down the X-axis
            pos = self.position.translate('x', float(x)).rotate90('y')
            ribs.append(Circle(radius=safe_r, position=pos, hidden=True))
        return ribs

    @Part(parse=False)
    def solid(self):
        return LoftedSolid(
            profiles=self.cross_sections,
            ruled=True,
            color=self.color,
            line_thickness=1e-9,
            isos=0
        )


class OptimizedResults(Base):
    """
    Handles optimized fuselage results, file generation, and STEP exports.
    """
    # Input parameters
    fuselage           = Input()
    r_optimized        = Input()
    fuselage_min_radii = Input()
    fuselage_max_radii = Input()
    wings_pair         = Input()
    vert_tail          = Input()
    hor_tail           = Input(None)
    include_hor_tail   = Input(True)
    fuselage_stations  = Input()

    @Attribute
    def optimized_fuselage_file(self):
        """Write out a temporary 'optimized_fuselage.txt' with 4 columns per line."""
        stations = self.fuselage_stations
        optimized_radii = self.r_optimized.tolist()
        min_radii = self.fuselage_min_radii
        max_radii = self.fuselage_max_radii

        tmp_path = os.path.join(os.getcwd(), "optimized_fuselage.txt")

        with open(tmp_path, "w") as f:
            for z, r_opt, r_min, r_max in zip(stations, optimized_radii, min_radii, max_radii):
                f.write(f"{z:.9f}\t{r_opt:.9f}\t{r_min:.9f}\t{r_max:.9f}\n")

        return tmp_path

    @action(label="Export Optimized Fuselage Data")
    def download_optimized_fuselage_data(self):
        """Export optimized fuselage data to Downloads folder."""
        try:
            del self.__dict__['optimized_fuselage_file']
        except KeyError:
            pass
        src = self.optimized_fuselage_file
        dest = os.path.join(os.path.expanduser("~"), "Downloads", "optimized_fuselage.txt")
        shutil.copy2(src, dest)
        os.remove(src)

    @Part(parse=False)
    def new_fuselage(self):
        """Create new fuselage using the continuous optimized data."""
        return OptimizedFuselage(
            xs=self.fuselage_stations,
            rs=self.r_optimized,
            color="deepskyblue"
        )

    @Part
    def optimized_aircraft(self):
        """Combine new optimized fuselage + same wings/tail to make a STEP-exportable solid."""
        return Compound(
            built_from=[
                self.new_fuselage.solid,
                self.wings_pair,
                self.vert_tail.solid,
                *(
                    [self.hor_tail]
                    if self.include_hor_tail
                    else []
                )
            ],
            color="white"
        )

    @action(label="Export Optimized Fuselage STEP")
    def step_file_optimized_fuselage(self):
        """Export optimized fuselage as STEP file."""
        dest = os.path.join(os.path.expanduser("~"), "Downloads", "optimized_fuselage.stp")
        writer = STEPWriter(nodes=[self.new_fuselage.solid], filename=dest)
        writer.write()

    @action(label="Export Optimized Aircraft STEP")
    def step_file_optimized_aircraft(self):
        """Export complete optimized aircraft as STEP file."""
        dest = os.path.join(os.path.expanduser("~"), "Downloads", "optimized_aircraft.stp")
        writer = STEPWriter(nodes=[self.optimized_aircraft], filename=dest)
        writer.write()