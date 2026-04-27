import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.interpolate import interp1d
from math import radians
from math import isclose
from parapy.geom import GeomBase, translate, rotate, ProjectedCurve, \
        MirroredShape, Rectangle, SubtractedSolid, Subtracted, Fused, \
        rotate90, Plane, Point, Vector, Compound, Box, Position
from parapy.geom.future import Common
from parapy.core import Input, Attribute, Part, child, action, DynamicType
from lifting_surface3 import LiftingSurface
from fuselage2 import Fuselage
from ref_frame import Frame


maindir = os.path.dirname(__file__)
import matlab.engine
eng = matlab.engine.start_matlab()
# Read the sheet, no header yet
df_raw = pd.read_excel(
    'primo funziona.xlsm',
    sheet_name='Fuselage Sections',
    header=None,
    engine='openpyxl'
)

# (Optional) grab other scalars:
fu_length_ = df_raw.iloc[1, 1]

# 1. Read Excel, using row-4 (0-indexed header=3) as column names
df_raw = pd.read_excel('primo funziona.xlsm', sheet_name='Fuselage Sections', header=None, engine='openpyxl')
header = df_raw.iloc[3].astype(str).str.strip().tolist()
df = df_raw.iloc[4:].copy()
df.columns = header
df = df[['x-Position (m)', 'Radius (m)', 'Minimum Radius (m)']].dropna()
df = df.rename(columns={'x-Position (m)': 'station', 'Radius (m)': 'radius', 'Minimum Radius (m)': 'constraint'})
df['station'] = df['station'].astype(float)
df['radius'] = df['radius'].astype(float)
df['constraint'] = df['constraint'].astype(float)
df.sort_values('station')

constraints_ = df['constraint'].to_numpy()
station_fu_ = df['station'].to_numpy()
radius_fu_ = df['radius'].to_numpy()



print('fu_length = ', fu_length_)

w_c_root_ = 0.12*fu_length_
w_c_tip_ = 0.048*fu_length_
t_factor_root_ = 0.01*fu_length_
t_factor_tip_ = 0.01*fu_length_
w_semi_span_ = 0.34*fu_length_
wing_position_fraction_long_ = 0.008*fu_length_
wing_position_fraction_vrt_ = 0.02*fu_length_
vt_long_ = 0.016*fu_length_
vt_taper_ = 0.008*fu_length_

vert_tail_file_= 'vert_tail.txt'
hor_tail_file_ = 'hor_tail.txt'


class Aircraft(GeomBase):
    fu_radius = Input(1)
    fu_sections = Input()
    fu_length = Input(fu_length_)
    airfoil_root = Input("whitcomb")
    airfoil_tip = Input("whitcomb")
    w_c_root = Input(w_c_root_)
    w_c_tip = Input(w_c_tip_)
    t_factor_root = Input(t_factor_root_)
    t_factor_tip = Input(t_factor_tip_)
    w_semi_span = Input(w_semi_span_)
    sweep = Input(40)
    twist = Input(-5)
    wing_dihedral = Input(3)
    wing_position_fraction_long = Input(wing_position_fraction_long_)
    wing_position_fraction_vrt = Input(wing_position_fraction_vrt_)
    vt_long = Input(vt_long_)
    vt_taper = Input(vt_taper_)
    mesh_deflection = Input(1e-4)
    radius_fu = Input(radius_fu_)
    station_fu = Input(station_fu_)
    constraints = Input(constraints_)
    vert_tail_file = Input(vert_tail_file_)
    hor_tail_file = Input(hor_tail_file_)
    include_tail = Input(False)

    @Part
    def aircraft_frame(self):
        return Frame(pos=self.position)

    @Part
    def fuselage(self):
        return Fuselage(
            station = self.station_fu,
            radius = self.radius_fu,
            color="Green"
        )

    @Part(settable=True)
    def new_fuselage(self):
        return Fuselage(
            station = self.station_fu,
            radius = self.radius_fu,
            color="Green"
        )

    @Part
    def right_wing(self):
        return LiftingSurface(
            x_offset=self.fu_length*0.4,
            z_offset=0,
            is_vertical=False
        )

    @Part
    def left_wing(self):
        return MirroredShape(
            shape_in=self.right_wing.solid,
            reference_point=self.position,
            vector1=self.position.Vz,
            vector2=self.position.Vx,
            mesh_deflection=self.mesh_deflection
        )


    @Part
    def vert_tail(self):
        return LiftingSurface(
            x_offset=self.fu_length * 0.88,
            wing_file=self.vert_tail_file,
            z_offset=0,
            is_vertical=True
        )


    @Part
    def h_tail_right(self):
        return LiftingSurface(
            x_offset=self.fu_length * 0.88,  # shift it downstream
            z_offset=0,
            wing_file=self.hor_tail_file,
            is_vertical=False,
            hidden = not self.include_tail
        )

    @Part
    def h_tail_left(self):
        return MirroredShape(
            shape_in=self.h_tail_right.solid,
            reference_point=self.position,
            vector1=self.position.Vz,
            vector2=self.position.Vx,
            mesh_deflection=self.mesh_deflection,
            hidden = not self.include_tail
        )



    @Part
    def left_wing_subtract(self):
        return SubtractedSolid(
            shape_in=self.left_wing,
            tool=self.fuselage.fuselage_solid,
            mesh_deflection=self.mesh_deflection,
            color="pink"
        )

    @Part
    def right_wing_subtract(self):
        return SubtractedSolid(
            shape_in=self.right_wing.solid,
            tool=self.fuselage.fuselage_solid,
            mesh_deflection=self.mesh_deflection,
            color="pink"
        )

    @Part
    def fuselage_less_wings(self):
        return Subtracted(
            shape_in=self.fuselage.fuselage_solid,
            tool=[self.right_wing, self.left_wing],
            mesh_deflection=self.mesh_deflection,
            color="orange"
        )

    @Part
    def right_wing_less_fuselage(self):
        return Subtracted(
            shape_in=self.right_wing.solid,
            tool=[self.fuselage.fuselage_solid],
            mesh_deflection=self.mesh_deflection,
            color="blue"
        )

    @Part
    def left_wing_less_fuselage(self):
        return Subtracted(
            shape_in=self.left_wing,
            tool=[self.fuselage.fuselage_solid],
            mesh_deflection=self.mesh_deflection,
            color="blue"
        )

    @Part
    def wings_less_fuselage(self):
        return Compound(
            [self.right_wing_less_fuselage,
            self.left_wing_less_fuselage],
            color="yellow"
        )

    @Part
    def boxetto(self):
        """car body"""
        return Box(length=0.1,
                   width=0.1,
                   height=0.1,
                   position = Position(Point(-2, 0,0)),
                   hidden = True
        )

    @Part
    def right_hor_tail_less_fus(self):
        return Subtracted(
            shape_in=self.h_tail_right.solid if self.include_tail else self.boxetto,
            tool=[self.fuselage.fuselage_solid],
            mesh_deflection=self.mesh_deflection,
            color="blue"
        )

    @Part
    def left_hor_tail_less_fus(self):
        return Subtracted(
            shape_in=self.h_tail_left if self.include_tail else self.boxetto,
            tool=[self.fuselage.fuselage_solid],
            mesh_deflection=self.mesh_deflection,
            color="blue"
        )

    @Part
    def vert_tail_less_fus(self):
        return Subtracted(
            shape_in=self.vert_tail.solid,
            tool=[self.fuselage.fuselage_solid],
            mesh_deflection=self.mesh_deflection,
            color="blue"
        )

    @Part
    def tail_less_fuselage(self):
        return Compound(
            [self.left_hor_tail_less_fus,
             self.right_hor_tail_less_fus,
             self.vert_tail_less_fus],
            color="yellow"
        )



    @Part
    def aircraft_solid(self):
        return Fused(
            shape_in=self.fuselage.fuselage_solid,
            tool=[
                self.left_wing,
                self.right_wing,
                self.vert_tail,
                self.h_tail_left,
                self.h_tail_right
            ],
            mesh_deflection=self.mesh_deflection,
            color="white"
        )




    #CROSS SECTIONAL AREAS
    @Part
    def b(self):
        return Plane(quantify=len(self.constraints)+1, reference=Point(child.index/len(self.constraints)*self.fu_length, 0, 0), normal=Vector(1, 0, 0))

    @Part
    def wings_cross_sectional_area(self):
        """Return the intersection of the wings"""
        return Common(quantify=len(self.constraints), args=[self.b[child.index]], tools=[self.wings_less_fuselage])

    @Part
    def tail_cross_sectional_area(self):
        """Return the intersection of the fuselage"""
        return Common(quantify=len(self.constraints), args=[self.b[child.index]], tools=[self.tail_less_fuselage if self.include_tail else self.vert_tail_less_fus])

    def fu_geom_cross_sect(self):
        """Return the geometric cross-sectional area of the fuselage."""
        return math.pi * self.radius_fu ** 2

    @Attribute
    def fuselage_cross_sectional_area(self):
        """Return the cross-sectional area of the fuselage from geometry instead of by using parapy (faster)."""
        return self.fu_geom_cross_sect()




    def choose_window_by_acf(self, x, threshold=1 / np.e):
        x = np.asarray(x)
        x = x - np.nanmean(x)
        corr = np.correlate(x, x, mode="full")
        acf = corr[len(x) - 1:] / corr[len(x) - 1]
        below = np.where(acf < threshold)[0]
        lag = below[0] if len(below) else 1
        win = max(1, lag)
        if win % 2 == 0:
            win += 1
        return win

    @Attribute(settable=True)
    def areas(self):
        return []

    @Attribute(settable=True)
    def x(self):
        return np.linspace(0, fu_length_, len(self.areas))


    @action(label='Wings cross sectional area graph')
    def graph_wings_cross_sectional_area(self):
        for sec in ac.wings_cross_sectional_area:
            try:
                self.areas.append(sec.faces[0].area + sec.faces[1].area)
            except (IndexError, AttributeError):
                self.areas.append(0)
        self.areas = np.array(self.areas)

        # — pick the full-strength window —
        auto_win = self.choose_window_by_acf(self.areas, threshold=0.1)

        half_win = max(1, int(np.ceil(auto_win * 0.7)))
        if half_win % 2 == 0:
            half_win += 1
        print(f"Smoothing strength window: {half_win}")

        # — apply the reduced smoothing —
        self.areas = (
            pd.Series(self.areas)
            .rolling(window=half_win, min_periods=1, center=True)
            .mean()
            .to_numpy()
        )

        # Plot original data
        plt.figure(figsize=(8, 4))
        plt.plot(self.x, self.areas, linestyle='-', label='Raw data')
        plt.xlabel('Fuselage axis position')
        plt.ylabel('Cross-sectional Area (units²)')
        plt.title('Wing Cross-Sectional Area')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

    @action(label='Total cross sectional area graph')
    def graph_total_cross_sectional_area(self):
        areas_fu = []
        self.areas_tail = []
        # fuselage cross-sectional area from geometry (should be faster)
        self.areas_fu = ac.fuselage_cross_sectional_area

        for sec in ac.tail_cross_sectional_area:
            try:
                # try to grab the second face’s area
                self.areas_tail.append(sec.faces[0].area + sec.faces[1].area + sec.faces[2].area) if self.include_tail else self.areas_tail.append(sec.faces[0].area)
            except (IndexError, AttributeError):
                # if faces[1] is out of range or missing, append zero
                self.areas_tail.append(0)

        # — pick the full-strength window —
        auto_win_tail = self.choose_window_by_acf(self.areas_tail, threshold=0.1)

        half_win_tail = max(1, int(np.ceil(auto_win_tail * 0.7)))
        if half_win_tail % 2 == 0:
            half_win_tail += 1
        print(f"Smoothing strength window: {half_win_tail}")

        self.areas_tail = (
            pd.Series(self.areas_tail)
            .rolling(window=half_win_tail, min_periods=1, center=True)
            .mean()
            .to_numpy()
        )

        self.areas_arr = np.array(self.areas)
        self.areas_fu_arr = np.array(self.areas_fu)
        self.areas_tail_arr = np.array(self.areas_tail)

        # elementwise sum
        areas_total = self.areas_arr + self.areas_fu_arr + self.areas_tail_arr  # length = N
        plt.figure(figsize=(10, 5))
        plt.plot(self.x, areas_total, linestyle='-', label='Raw data')
        plt.xlabel('Fuselage axis position')
        plt.ylabel('Cross-sectional Area (units²)')
        plt.title('Combined Cross-Sectional Area')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()


    #Method that calls the MATLAB optimizator
    def call_optimizator(self):
        z_ml = matlab.double(self.x)
        wing_ml = matlab.double(self.areas)
        tail_ml = matlab.double(self.areas_tail)
        fus_ml = matlab.double(self.areas_fu)
        constr_ml = matlab.double(self.constraints)

        outputs = eng.fuselage_optimizer(z_ml, wing_ml, tail_ml, fus_ml, constr_ml, nargout=10)
        # Extract optimized fuselage areas
        self.Af_0 = outputs[8]
        self.Af_opt = outputs[9]

        # Reconstruct optimized and initial total distributions
        self.total_initial = outputs[0]
        self.total_optimized = outputs[1]

        self.tot_in_sq = np.squeeze(self.total_initial)  # or total_initial.flatten()
        self.tot_opt_sq = np.squeeze(self.total_optimized)  # or total_optimized.flatten()

        self.Af_0_sq = np.squeeze(self.Af_0)  # or total_initial.flatten()
        self.Af_opt_sq = np.squeeze(self.Af_opt)  # or total_optimized.flatten()

        self.Af_0_comp = np.array(self.Af_0).astype(float).flatten()
        self.Af_opt_comp = np.array(self.Af_opt).astype(float).flatten()
        # Compute radii
        self.r_initial = np.sqrt(self.Af_0_comp / np.pi)
        self.r_optimized = np.sqrt(self.Af_opt_comp / np.pi)
        n_theta = 100
        self.theta = np.linspace(0, 2 * np.pi, n_theta)
        self.Zc = np.tile(self.x, (n_theta, 1)).T
        self.X0 = np.outer(self.r_initial, np.cos(self.theta))
        self.Y0 = np.outer(self.r_initial, np.sin(self.theta))
        self.Xopt = np.outer(self.r_optimized, np.cos(self.theta)) + 3 * np.max(self.r_initial)
        self.Yopt = np.outer(self.r_optimized, np.sin(self.theta))

        self.new_fuselage = Fuselage(station = self.station_fu,
                                     radius = self.r_optimized,
                                     color="red",
                                     transparency=0
        )


    @action(label='Initial vs optimized fuselage area distribution')
    def graph_init_opt_fus_cross_sect_area(self):
        self.call_optimizator()
        # Plot Fuselage-Only Distribution: Initial vs Optimized
        plt.figure(figsize=(10, 5))
        plt.plot(self.x.T, self.Af_0_sq, 'b--', linewidth=1.5, label='Initial fuselage')
        plt.plot(self.x.T, self.Af_opt_sq, 'r-', linewidth=2, label='Optimized fuselage')
        plt.xlabel('Station z (m)')
        plt.ylabel('Fuselage Area A_f(z) (m^2)')
        plt.title('Fuselage Area Distribution: Initial vs. Optimized')
        plt.legend(loc='best')
        plt.grid(True)
        plt.tight_layout()
        plt.show()


    @action(label='Initial vs optimized total area distribution')
    def graph_init_opt_tot_cross_sect_area(self):
        # Plot Total Area Distribution: Initial vs Optimized
        plt.figure(figsize=(10, 5))
        plt.plot(self.x, self.tot_in_sq, 'b--', linewidth=1.5, label='Initial')
        plt.plot(self.x, self.tot_opt_sq, 'r-', linewidth=2, label='Optimized')
        plt.xlabel('Station z (m)')
        plt.ylabel('Total Area A_total(z) (m^2)')
        plt.title('Total Area Distribution: Initial vs. Optimized')
        plt.legend(loc='best')
        plt.grid(True)
        plt.tight_layout()
        plt.show()


    @action(label='3-D view of initial vs optimized fuselage')
    def td_graph_init_opt_fuselage(self):
        x_limits = (np.min([self.X0.min(), self.Xopt.min()]), np.max([self.X0.max(), self.Xopt.max()]))
        y_limits = (np.min([self.Y0.min(), self.Yopt.min()]), np.max([self.Y0.max(), self.Yopt.max()]))
        z_limits = (self.Zc.min(), self.Zc.max())

        fig = plt.figure(figsize=(12, 6))
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(self.X0, self.Y0, self.Zc, alpha=0.7, rstride=5, cstride=5, linewidth=0)
        ax.plot_surface(self.Xopt, self.Yopt, self.Zc, alpha=0.7, rstride=5, cstride=5, linewidth=0)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z (Station Index)')
        ax.set_title('3D view of the fuselages')
        ax.set_box_aspect((1, (y_limits[1] - y_limits[0]) / (x_limits[1] - x_limits[0]),
                           (z_limits[1] - z_limits[0]) / (x_limits[1] - x_limits[0])))
        plt.tight_layout()
        plt.show()





if __name__ == '__main__':
    from parapy.gui import display
    print("Creating aircraft...")
    ac = Aircraft()
    display(ac)

