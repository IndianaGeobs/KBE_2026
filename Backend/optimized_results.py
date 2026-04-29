import os
import shutil
from parapy.core import Base, Input, Attribute, Part, action
from parapy.geom import Compound
from parapy.exchange.step import STEPWriter

from Backend.fuselage import Fuselage

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

    @Attribute
    def optimized_fuselage_file(self):
        """Write out a temporary 'optimized_fuselage.txt' with 4 columns per line."""
        stations = [pt[2] for pt in self.fuselage.revolution_curve.points]
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
        """Create new fuselage using optimized data."""
        return Fuselage(fuselage_file=self.optimized_fuselage_file, max_revolution_curve_degree=2, color="deepskyblue")

    @Part
    def optimized_aircraft(self):
        """Combine new optimized fuselage + same wings/tail to make a STEP‐exportable solid."""
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