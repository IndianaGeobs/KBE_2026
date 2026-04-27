import os

from lifting_surface_reader import get_wing_data

from parapy.core import Part, Input, Attribute, child
from parapy.geom import GeomBase, Point, FittedCurve, LoftedSolid, translate

class LiftingSurface(GeomBase):
    """Loads wing-station DAT files, applies chord & twist, and creates one
    FittedCurve per station—all in one go."""
    wing_file = Input('wing.txt')
    x_offset = Input(1)
    z_offset = Input(1)
    is_vertical = Input(False)

    @Attribute
    def points(self):
        station_pts = get_wing_data(self.wing_file)[0]

        out = []
        for pts in station_pts:
            station_list = []
            for x0, y0, z0 in pts:
                # vertical wing? rotate only:
                if self.is_vertical:
                    x1, y1, z1 = x0, -z0, y0
                else:
                    x1, y1, z1 = x0, y0, z0

                # apply offsets:
                station_list.append(
                    Point(x1 + self.x_offset,
                          y1,
                          z1 + self.z_offset)
                )
            out.append(station_list)

        return out

        return station_points_list


    @Part
    def airfoil_curves(self):
        """One FittedCurve per station, all instantiated ‘at once’."""
        return FittedCurve(points=self.points[child.index],
                           quantify=get_wing_data(self.wing_file)[1], tolerance = 0.01)

    @Part
    def solid(self):
        return LoftedSolid(
            profiles=self.airfoil_curves,
            ruled = True,
            
        )

    @Attribute
    def error_lifting_surface(self):
        error_lift = get_wing_data(self.wing_file)[2]
        return error_lift



if __name__ == '__main__':
    from parapy.gui import display

    lifting_surface = LiftingSurface()
    display(lifting_surface)


