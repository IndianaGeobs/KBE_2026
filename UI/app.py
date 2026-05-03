import io
import base64
import urllib.parse
import matplotlib.pyplot as plt

from parapy.webgui import layout, viewer, mui, html
from parapy.webgui.core import Component, NodeType, State, update
from parapy.webgui.app_bar import AppBar

from area_rule import AR, PREVIEW_AR
from inputs_panel import InputsPanel
#from Backend.ghost_geometry import GHOST


class App(Component):
    """App: batches uploads + Apply & Render"""
    applying = State(False)
    busy = State(False)
    page = State(0)
    fig_images = State([])

    # --- UI Visibility State ---
    show_inputs = State(True)

    # Dialog states
    dialog_open_wing_out_fus = State(False)
    dialog_open_wing_hor_tail_inters = State(False)
    dialog_open_wing_vert_tail_inters = State(False)
    dialog_open_hor_tail_vert_tail_inters = State(False)
    dialog_open_ht_out_fus = State(False)
    dialog_open_vt_out_fus = State(False)
    dialog_open_wing_tip = State(False)
    dialog_open_ht_tip = State(False)
    dialog_open_vt_tip = State(False)
    dialog_open_fuselage_reading_error = State(False)
    dialog_open_lifting_surface_reading_error = State(False)
    dialog_open_wing_new_fus_error = State(False)
    dialog_open_ht_new_fus_error = State(False)
    dialog_open_vt_new_fus_error = State(False)

    # Last‐committed snapshots
    last_wing_file = State(AR.wing_file)
    last_vert_tail_file = State(AR.vert_tail_file)
    last_hor_tail_file = State(AR.hor_tail_file)
    last_fuselage_file = State(AR.fuselage_file)

    _total = AR.nose_length + AR.main_body_length + AR.tail_length

    last_x_offs_wings = State(AR.x_offs_wings)
    last_z_offs_wings = State(AR.z_offs_wings)
    last_x_offs_tail = State(AR.x_offs_tail)
    last_z_offs_tail = State(AR.z_offs_tail)
    last_x_offs_vert_tail = State(AR.x_offs_vert_tail)
    last_z_offs_vert_tail = State(AR.z_offs_vert_tail)

    inputs_panel = State(None)

    # --- Toggle UI Panel ---
    def toggle_inputs(self, *args):
        self.show_inputs = not self.show_inputs
        update()

    def on_file1_uploaded(self, path):
        self.inputs_panel.pending_wing_file = path

    def on_file2_uploaded(self, path):
        self.inputs_panel.pending_vert_tail_file = path

    def on_file3_uploaded(self, path):
        self.inputs_panel.pending_hor_tail_file = path

    def on_file4_uploaded(self, path):
        self.inputs_panel.pending_fuselage_file = path

    # Helper functions for ratio to absolute values of lifting surfaces offsets

    def _to_abs(self, x_offs, z_offs):
        total_length = AR.nose_length + AR.main_body_length + AR.tail_length
        return x_offs * total_length, z_offs * AR.fuselage_radius

    def _to_ratio(self, x_offs, z_offs, nose, body, tail, radius):
        return x_offs / (nose + body + tail), z_offs / radius

    def apply_changes(self, *args):
        self.applying = True
        update()

        try:
            panel = self.inputs_panel

            old = {
                "wing_file": self.last_wing_file,
                "vert_tail_file": self.last_vert_tail_file,
                "hor_tail_file": self.last_hor_tail_file,
                "fuselage_file": self.last_fuselage_file,
                "x_offs_wings": self.last_x_offs_wings,
                "z_offs_wings": self.last_z_offs_wings,
                "x_offs_tail": self.last_x_offs_tail,
                "z_offs_tail": self.last_z_offs_tail,
                "x_offs_vert_tail": self.last_x_offs_vert_tail,
                "z_offs_vert_tail": self.last_z_offs_vert_tail,
                "include_hor_tail": AR.include_hor_tail,
            }

            try:
                # Original Offsets
                new_x_offs_wings = float(panel.pending_x_offs_wings)
                new_z_offs_wings = float(panel.pending_z_offs_wings)
                new_x_offs_tail = float(panel.pending_x_offs_tail)
                new_z_offs_tail = float(panel.pending_z_offs_tail)
                new_x_offs_vert = float(panel.pending_x_offs_vert_tail)
                new_z_offs_vert = float(panel.pending_z_offs_vert_tail)

                # Fuselage
                new_nose_length = float(panel.pending_nose_length)
                new_body_length = float(panel.pending_main_body_length)
                new_tail_length = float(panel.pending_tail_length)
                new_radius = float(panel.pending_fuselage_radius)

                # Wing
                new_wing_dihedral = float(panel.pending_wing_dihedral)
                new_wing_root_chord = float(panel.pending_wing_root_chord)
                new_wing_sections = panel.pending_wing_sections

                # --- NEW VERTICAL TAIL ---
                new_vt_root = float(panel.pending_vt_root_chord)
                new_vt_span = float(panel.pending_vt_span)
                new_vt_tip = float(panel.pending_vt_tip_chord)
                new_vt_sweep = float(panel.pending_vt_sweep)

                # --- NEW HORIZONTAL TAIL ---
                new_ht_root = float(panel.pending_ht_root_chord)
                new_ht_span = float(panel.pending_ht_span)
                new_ht_tip = float(panel.pending_ht_tip_chord)
                new_ht_sweep = float(panel.pending_ht_sweep)

            except ValueError:
                self._revert_to_last_committed(panel, old)
                panel.error_wing = True
                panel.error_wing_tip = True
                return

            new_include_hor_tail = panel.pending_include_hor_tail


            try:
                from area_rule import AreaRule
                temp_AR = AreaRule(
                    fuselage_file=panel.pending_fuselage_file or old["fuselage_file"],
                    wing_file=panel.pending_wing_file or old["wing_file"],
                    vert_tail_file=panel.pending_vert_tail_file or old["vert_tail_file"],
                    hor_tail_file=panel.pending_hor_tail_file or old["hor_tail_file"],
                    include_hor_tail=new_include_hor_tail,
                    x_offs_wings=new_x_offs_wings,
                    z_offs_wings=new_z_offs_wings,
                    x_offs_tail=new_x_offs_tail,
                    z_offs_tail=new_z_offs_tail,
                    x_offs_vert_tail=new_x_offs_vert,
                    z_offs_vert_tail=new_z_offs_vert,
                    vt_root_chord_ratio=new_vt_root,
                    vt_span_ratio=new_vt_span,
                    vt_tip_chord_ratio=new_vt_tip,
                    vt_sweep=new_vt_sweep,
                    ht_root_chord_ratio=new_ht_root,
                    ht_span_ratio=new_ht_span,
                    ht_tip_chord_ratio=new_ht_tip,
                    ht_sweep=new_ht_sweep,
                    show_constraints=AR.show_constraints,
                    nose_length=new_nose_length,
                    main_body_length=new_body_length,
                    tail_length=new_tail_length,
                    fuselage_radius=new_radius,
                    user_constraints=panel.pending_user_constraints,
                    wing_dihedral=new_wing_dihedral,
                    wing_root_chord_ratio=new_wing_root_chord,
                    wing_sections_ratios=new_wing_sections
                )

                fuselage_reading_error = temp_AR.aircraft.intersection_checker.fuselage_reading_error_status
                lifting_surface_reading_error = temp_AR.aircraft.intersection_checker.lifting_surface_reading_error_status

                if fuselage_reading_error or lifting_surface_reading_error:
                    self._handle_reading_errors(panel, old, fuselage_reading_error, lifting_surface_reading_error)
                    return

                validation_errors = self._check_geometry_intersections(temp_AR, panel, old)
                if validation_errors:
                    # return
                    pass

            except Exception as e:
                import traceback
                print("Unexpected error in AreaRule validation:", e)
                traceback.print_exc()
                self._handle_unexpected_error(panel, old)
                return

            self._apply_validated_changes(panel, old, new_x_offs_wings, new_z_offs_wings,
                                          new_x_offs_tail, new_z_offs_tail, new_x_offs_vert, new_z_offs_vert,
                                          new_include_hor_tail, new_tail_length, new_body_length, new_nose_length,
                                          new_radius, new_wing_dihedral, new_wing_root_chord, new_wing_sections,
                                          new_vt_root, new_vt_span, new_vt_tip, new_vt_sweep,new_ht_root,
                                          new_ht_span, new_ht_tip, new_ht_sweep)
        finally:
            self.applying = False

    def _revert_to_last_committed(self, panel, old):
        panel.pending_wing_file = old["wing_file"]
        panel.pending_vert_tail_file = old["vert_tail_file"]
        panel.pending_hor_tail_file = old["hor_tail_file"]
        panel.pending_fuselage_file = old["fuselage_file"]
        panel.pending_x_offs_wings = str(old["x_offs_wings"])
        panel.pending_z_offs_wings = str(old["z_offs_wings"])
        panel.pending_x_offs_tail = str(old["x_offs_tail"])
        panel.pending_z_offs_tail = str(old["z_offs_tail"])
        panel.pending_x_offs_vert_tail = str(old["x_offs_vert_tail"])
        panel.pending_z_offs_vert_tail = str(old["z_offs_vert_tail"])
        panel.pending_include_hor_tail = old["include_hor_tail"]
        panel.request_upload_reset()

    def _handle_reading_errors(self, panel, old, fuselage_reading_error, lifting_surface_reading_error):
        self._revert_to_last_committed(panel, old)
        self._clear_all_error_flags(panel)
        if fuselage_reading_error:
            panel.fuselage_reading_error = fuselage_reading_error
            self.dialog_open_fuselage_reading_error = True
        if lifting_surface_reading_error:
            panel.lifting_surface_reading_error = lifting_surface_reading_error
            self.dialog_open_lifting_surface_reading_error = True

    def _check_geometry_intersections(self, temp_AR, panel, old):
        try:
            _ = temp_AR.aircraft.wings_pair
            _ = temp_AR.aircraft.fuselage
            _ = temp_AR.aircraft.vert_tail
            _ = temp_AR.aircraft.wings_less_fuselage
            _ = temp_AR.aircraft.vert_tail_less_fuselage
            if temp_AR.include_hor_tail and (panel.pending_hor_tail_file or old["hor_tail_file"]):
                _ = temp_AR.aircraft.hor_tail

            wing_fuselage_err = temp_AR.aircraft.intersection_checker.wing_fuselage_intersection_status
            vert_fuselage_err = temp_AR.aircraft.intersection_checker.vert_tail_fuselage_intersection_status
            wing_tip_error = temp_AR.aircraft.intersection_checker.wing_tip_out_fus_status
            vt_tip_error = temp_AR.aircraft.intersection_checker.vert_tip_out_fus_status
            wing_vt_error = temp_AR.aircraft.intersection_checker.wing_vert_tail_intersection_status

            wing_hor_tail_err = False
            ht_fuselage_err = False
            ht_tip_error = False
            ht_vt_error = False

            if temp_AR.include_hor_tail and (panel.pending_hor_tail_file or old["hor_tail_file"]):
                try:
                    wing_hor_tail_err = temp_AR.aircraft.intersection_checker.wing_hor_tail_intersection_status
                    ht_fuselage_err = temp_AR.aircraft.intersection_checker.hor_tail_fuselage_intersection_status
                    ht_tip_error = temp_AR.aircraft.intersection_checker.hor_tail_tip_out_fus_status
                    ht_vt_error = temp_AR.aircraft.intersection_checker.hor_tail_vert_tail_intersection_status
                except Exception:
                    pass

            if any([wing_fuselage_err, wing_hor_tail_err, vert_fuselage_err, ht_fuselage_err,
                    wing_tip_error, ht_tip_error, vt_tip_error, wing_vt_error, ht_vt_error]):
                self._revert_to_last_committed(panel, old)
                self._clear_all_error_flags(panel)
                self._set_geometry_error_flags(panel, wing_fuselage_err, wing_hor_tail_err,
                                               vert_fuselage_err, ht_fuselage_err, wing_tip_error,
                                               ht_tip_error, vt_tip_error, wing_vt_error, ht_vt_error)
                return True

            return False

        except Exception as e:
            print(f"Geometry creation error: {e}")
            self._handle_unexpected_error(panel, old)
            return True

    def _clear_all_error_flags(self, panel):
        panel.error_wing = False
        panel.error_vert_tail = False
        panel.error_hor_tail = False
        panel.error_fuselage = False
        panel.error_wing_tip = False
        panel.error_ht_tip = False
        panel.error_vt_tip = False
        panel.error_wing_vt_intersection = False
        panel.error_ht_vt_intersection = False
        panel.error_hor_tail_over_wing = False
        panel.fuselage_reading_error = False
        panel.lifting_surface_reading_error = False

    def _set_geometry_error_flags(self, panel, wing_fuselage_err, wing_hor_tail_err, vert_fuselage_err,
                                  ht_fuselage_err, wing_tip_error, ht_tip_error, vt_tip_error,
                                  wing_vt_error, ht_vt_error):
        if wing_fuselage_err:
            panel.error_wing = wing_fuselage_err
            self.dialog_open_wing_out_fus = True
        if wing_hor_tail_err:
            panel.error_hor_tail_over_wing = wing_hor_tail_err
            self.dialog_open_wing_hor_tail_inters = True
        if ht_fuselage_err:
            panel.error_hor_tail = ht_fuselage_err
            self.dialog_open_ht_out_fus = True
        if vert_fuselage_err:
            panel.error_vert_tail = vert_fuselage_err
            self.dialog_open_vt_out_fus = True
        if wing_tip_error:
            panel.error_wing_tip = wing_tip_error
            self.dialog_open_wing_tip = True
        if ht_tip_error:
            panel.error_ht_tip = ht_tip_error
            self.dialog_open_ht_tip = True
        if vt_tip_error:
            panel.error_vt_tip = vt_tip_error
            self.dialog_open_vt_tip = True
        if wing_vt_error:
            panel.error_wing_vt_intersection = wing_vt_error
            self.dialog_open_wing_vert_tail_inters = True
        if ht_vt_error:
            panel.error_ht_vt_intersection = ht_vt_error
            self.dialog_open_hor_tail_vert_tail_inters = True

        panel.error_fuselage = wing_fuselage_err or ht_fuselage_err or vert_fuselage_err

    def _handle_unexpected_error(self, panel, old):
        self._revert_to_last_committed(panel, old)
        files_changed = {
            'wing': panel.pending_wing_file != old["wing_file"],
            'vert_tail': panel.pending_vert_tail_file != old["vert_tail_file"],
            'hor_tail': panel.pending_hor_tail_file != old["hor_tail_file"],
            'fuselage': panel.pending_fuselage_file != old["fuselage_file"]
        }
        self._clear_all_error_flags(panel)

        if files_changed['wing']:
            panel.error_wing = True
            panel.error_wing_tip = True
        if files_changed['vert_tail']:
            panel.error_vert_tail = True
            panel.error_vt_tip = True
        if files_changed['hor_tail']:
            panel.error_hor_tail = True
            panel.error_ht_tip = True
        if files_changed['fuselage']:
            panel.error_fuselage = True

        if not any(files_changed.values()):
            panel.error_wing = True
            panel.error_vert_tail = True
            panel.error_hor_tail = True
            panel.error_fuselage = True
            panel.error_wing_tip = True
            panel.error_ht_tip = True
            panel.error_vt_tip = True
            panel.error_wing_vt_intersection = True
            panel.error_ht_vt_intersection = True

        self.dialog_open_wing_out_fus = True

    def _apply_validated_changes(self, panel, old,
                                 new_x_offs_wings, new_z_offs_wings,
                                 new_x_offs_tail, new_z_offs_tail,
                                 new_x_offs_vert, new_z_offs_vert,
                                 new_include_hor_tail, new_tail_length, new_body_length, new_nose_length, new_radius,
                                 new_wing_dihedral, new_wing_root_chord, new_wing_sections,
                                 # --- ACCEPT THE NEW VARIABLES HERE ---
                                 new_vt_root, new_vt_span, new_vt_tip, new_vt_sweep,
                                 new_ht_root, new_ht_span, new_ht_tip, new_ht_sweep):

        AR.wing_file = panel.pending_wing_file or old["wing_file"]
        AR.vert_tail_file = panel.pending_vert_tail_file or old["vert_tail_file"]
        AR.hor_tail_file = panel.pending_hor_tail_file or old["hor_tail_file"]
        AR.fuselage_file = panel.pending_fuselage_file or old["fuselage_file"]
        AR.include_hor_tail = new_include_hor_tail

        AR.x_offs_wings = new_x_offs_wings
        AR.z_offs_wings = new_z_offs_wings
        AR.x_offs_tail = new_x_offs_tail
        AR.z_offs_tail = new_z_offs_tail
        AR.x_offs_vert_tail = new_x_offs_vert
        AR.z_offs_vert_tail = new_z_offs_vert

        AR.wing_dihedral = new_wing_dihedral
        AR.wing_root_chord_ratio = new_wing_root_chord
        AR.wing_sections_ratios = new_wing_sections

        AR.vt_root_chord_ratio = new_vt_root
        AR.vt_span_ratio = new_vt_span
        AR.vt_tip_chord_ratio = new_vt_tip
        AR.vt_sweep = new_vt_sweep

        AR.ht_root_chord_ratio = new_ht_root
        AR.ht_span_ratio = new_ht_span
        AR.ht_tip_chord_ratio = new_ht_tip
        AR.ht_sweep = new_ht_sweep

        AR.user_constraints = panel.pending_user_constraints
        self.last_user_constraints = AR.user_constraints

        self.last_x_offs_wings = new_x_offs_wings
        self.last_z_offs_wings = new_z_offs_wings
        self.last_x_offs_tail = new_x_offs_tail
        self.last_z_offs_tail = new_z_offs_tail
        self.last_x_offs_vert_tail = new_x_offs_vert
        self.last_z_offs_vert_tail = new_z_offs_vert

        self.last_wing_dihedral = new_wing_dihedral
        self.last_wing_root_chord = new_wing_root_chord
        self.last_wing_sections = new_wing_sections

        AR.nose_length = new_nose_length
        AR.main_body_length = new_body_length
        AR.tail_length = new_tail_length
        AR.fuselage_radius = new_radius

        self.last_wing_file = AR.wing_file
        self.last_vert_tail_file = AR.vert_tail_file
        self.last_hor_tail_file = AR.hor_tail_file
        self.last_fuselage_file = AR.fuselage_file

        self._clear_all_error_flags(panel)

    def handle_close_wing_out_fus(self, *args):
        self.dialog_open_wing_out_fus = False

    def handle_close_ht_out_fus(self, *args):
        self.dialog_open_ht_out_fus = False

    def handle_close_vt_out_fus(self, *args):
        self.dialog_open_vt_out_fus = False

    def handle_close_lift_surf_inters(self, *args):
        self.dialog_open_wing_hor_tail_inters = False

    def handle_close_wing_tip(self, *args):
        self.dialog_open_wing_tip = False

    def handle_close_ht_tip(self, *args):
        self.dialog_open_ht_tip = False

    def handle_close_vt_tip(self, *args):
        self.dialog_open_vt_tip = False

    def handle_close_wing_vt_inters(self, *args):
        self.dialog_open_wing_vert_tail_inters = False

    def handle_close_ht_vt_intersection(self, *args):
        self.dialog_open_hor_tail_vert_tail_inters = False

    def handle_close_fuselage_reading_error(self, *args):
        self.dialog_open_fuselage_reading_error = False

    def handle_close_lifting_surface_reading_error(self, *args):
        self.dialog_open_lifting_surface_reading_error = False

    def handle_close_wing_new_fus_error(self, *args):
        try:
            plt.close('all')
        except:
            pass
        self.dialog_open_wing_new_fus_error = False
        update()

    def handle_close_ht_new_fus_error(self, *args):
        try:
            plt.close('all')
        except:
            pass
        self.dialog_open_ht_new_fus_error = False
        update()

    def handle_close_vt_new_fus_error(self, *args):
        try:
            plt.close('all')
        except:
            pass
        self.dialog_open_vt_new_fus_error = False
        update()

    def run_calculation(self, *args):
        self.busy = True
        update()

        try:
            figs = AR.aircraft.show_all_plots()
            self.fig_images = []

            for idx, fig in enumerate(figs):
                try:
                    buf = io.BytesIO()
                    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
                    buf.seek(0)
                    img_b64 = base64.b64encode(buf.read()).decode()
                    self.fig_images.append({
                        "src": f"data:image/png;base64,{img_b64}",
                        "filename": f"graph_{idx + 1}.png"
                    })
                    buf.close()
                except Exception as fig_error:
                    print(f"Error processing figure {idx}: {fig_error}")
                finally:
                    try:
                        plt.close(fig)
                    except:
                        pass

            plt.close('all')

            post_opt_errors = self._check_post_optimization_errors()

            if post_opt_errors:
                # ERROR FOUND: Jump straight to the 3D View (Page 2)
                # so the user can visually inspect the broken wing/tail root!
                self.page = 2
            else:
                # SUCCESS: Jump to the Results/Graphs (Page 1)
                self.page = 1

        except Exception as e:
            print(f"Error during optimization: {e}")
            import traceback
            traceback.print_exc()
            try:
                plt.close('all')
            except:
                pass
        finally:
            # This ensures the loading spinner turns off and the UI updates
            # regardless of whether it succeeded, failed, or crashed.
            self.busy = False
            update()

    def _check_post_optimization_errors(self):
        has_errors = False
        if AR.aircraft.optimized_intersection_checker.wing_fuselage_intersection_new_status:
            self.dialog_open_wing_new_fus_error = True
            has_errors = True
        if (AR.include_hor_tail and
                hasattr(AR.aircraft, 'hor_tail_fuselage_intersection_new_status') and
                AR.aircraft.optimized_intersection_checker.hor_tail_fuselage_intersection_new_status):
            self.dialog_open_ht_new_fus_error = True
            has_errors = True
        if (hasattr(AR.aircraft, 'vert_tail_fuselage_intersection_new_status') and
                AR.aircraft.optimized_intersection_checker.vert_tail_fuselage_intersection_new_status):
            self.dialog_open_vt_new_fus_error = True
            has_errors = True
        return has_errors

    def switch_to_graphs(self, *args):
        self.page = 1
        update()

    def switch_to_view3d(self, *args):
        self.page = 2
        update()

    def toggle_constraints(self, *args):
        AR.show_constraints = not AR.show_constraints
        update()

    def render(self) -> NodeType:
        inputs = InputsPanel(
            on_upload1=self.on_file1_uploaded,
            on_upload2=self.on_file2_uploaded,
            on_upload3=self.on_file3_uploaded,
            on_upload4=self.on_file4_uploaded,
            # --- PASSING THE BUTTON PROPS ---
            on_close=self.toggle_inputs,
            on_apply=self.apply_changes,
            is_applying=self.applying,
            on_optimize=self.run_calculation,
            is_busy=self.busy
            # --------------------------------
        )
        self.inputs_panel = inputs

        # --- EXTRACTED DIALOGS ---
        dialogs = [
            mui.Dialog(open=self.dialog_open_wing_out_fus, onClose=self.handle_close_wing_out_fus)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'warning.main', 'mb': 1})['⚠️'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'error.main', 'pt': 0, 'pb': 1})['Configuration Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['Part of the wings surfaces\' roots is outside of the fuselage'],
                    mui.DialogContentText['Fix the geometry to run the optimization']
                ],
                mui.DialogActions[mui.Button(onClick=self.handle_close_wing_out_fus, color='error')['Ok']]
            ],
            mui.Dialog(open=self.dialog_open_ht_out_fus, onClose=self.handle_close_ht_out_fus)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'warning.main', 'mb': 1})['⚠️'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'error.main', 'pt': 0, 'pb': 1})['Configuration Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['Part of the horizontal tail\'s root is outside of the fuselage'],
                    mui.DialogContentText['Fix the geometry to run the optimization']
                ],
                mui.DialogActions[mui.Button(onClick=self.handle_close_ht_out_fus, color='error')['Ok']]
            ],
            mui.Dialog(open=self.dialog_open_vt_out_fus, onClose=self.handle_close_vt_out_fus)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'warning.main', 'mb': 1})['⚠️'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'error.main', 'pt': 0, 'pb': 1})['Configuration Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['Part of the vertical tail\'s root is outside of the fuselage'],
                    mui.DialogContentText['Fix the geometry to run the optimization']
                ],
                mui.DialogActions[mui.Button(onClick=self.handle_close_vt_out_fus, color='error')['Ok']]
            ],
            mui.Dialog(open=self.dialog_open_wing_hor_tail_inters, onClose=self.handle_close_lift_surf_inters)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'warning.main', 'mb': 1})['⚠️'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'error.main', 'pt': 0, 'pb': 1})['Configuration Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['Two lifting surfaces are intersecting'],
                    mui.DialogContentText['Fix the geometry to run the optimization']
                ],
                mui.DialogActions[mui.Button(onClick=self.handle_close_lift_surf_inters, color='error')['Ok']]
            ],
            mui.Dialog(open=self.dialog_open_wing_tip, onClose=self.handle_close_wing_tip)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'warning.main', 'mb': 1})['⚠️'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'error.main', 'pt': 0, 'pb': 1})['Configuration Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['Part of the wing is not within the fuselage range'],
                    mui.DialogContentText['Fix the geometry to run the optimization']
                ],
                mui.DialogActions[mui.Button(onClick=self.handle_close_wing_tip, color='error')['Ok']]
            ],
            mui.Dialog(open=self.dialog_open_ht_tip, onClose=self.handle_close_ht_tip)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'warning.main', 'mb': 1})['⚠️'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'error.main', 'pt': 0, 'pb': 1})['Configuration Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['Part of the horizontal tail is not within the fuselage range'],
                    mui.DialogContentText['Fix the geometry to run the optimization']
                ],
                mui.DialogActions[mui.Button(onClick=self.handle_close_ht_tip, color='error')['Ok']]
            ],
            mui.Dialog(open=self.dialog_open_vt_tip, onClose=self.handle_close_vt_tip)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'warning.main', 'mb': 1})['⚠️'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'error.main', 'pt': 0, 'pb': 1})['Configuration Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['Part of the vertical tail is not within the fuselage range'],
                    mui.DialogContentText['Fix the geometry to run the optimization']
                ],
                mui.DialogActions[mui.Button(onClick=self.handle_close_vt_tip, color='error')['Ok']]
            ],
            mui.Dialog(open=self.dialog_open_wing_vert_tail_inters, onClose=self.handle_close_wing_vt_inters)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'warning.main', 'mb': 1})['⚠️'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'error.main', 'pt': 0, 'pb': 1})['Configuration Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['Part of the wings and the vertical tail are intersecting'],
                    mui.DialogContentText['Fix the geometry to run the optimization']
                ],
                mui.DialogActions[mui.Button(onClick=self.handle_close_wing_vt_inters, color='error')['Ok']]
            ],
            mui.Dialog(open=self.dialog_open_hor_tail_vert_tail_inters, onClose=self.handle_close_ht_vt_intersection)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'warning.main', 'mb': 1})['⚠️'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'error.main', 'pt': 0, 'pb': 1})['Configuration Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['Part of the horizontal tail and the vertical tail are intersecting'],
                    mui.DialogContentText['Fix the geometry to run the optimization']
                ],
                mui.DialogActions[mui.Button(onClick=self.handle_close_ht_vt_intersection, color='error')['Ok']]
            ],
            mui.Dialog(open=self.dialog_open_fuselage_reading_error, onClose=self.handle_close_fuselage_reading_error)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'warning.main', 'mb': 1})['⚠️'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'warning.main', 'pt': 0, 'pb': 1})['Reading Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['Error reading the fuselage file'],
                    mui.DialogContentText['Fix the fuselage file to run the optimization']
                ],
                mui.DialogActions[mui.Button(onClick=self.handle_close_fuselage_reading_error, color='warning')['Ok']]
            ],
            mui.Dialog(open=self.dialog_open_lifting_surface_reading_error,
                       onClose=self.handle_close_lifting_surface_reading_error)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'warning.main', 'mb': 1})['⚠️'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'warning.main', 'pt': 0, 'pb': 1})['Reading Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['Error reading one of the lifting surfaces files'],
                    mui.DialogContentText['Fix the lifting surface file to run the optimization']
                ],
                mui.DialogActions[
                    mui.Button(onClick=self.handle_close_lifting_surface_reading_error, color='warning')['Ok']]
            ],
            mui.Dialog(open=self.dialog_open_wing_new_fus_error, onClose=self.handle_close_wing_new_fus_error)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'error.main', 'mb': 1})['🔴'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'error.main', 'pt': 0, 'pb': 1})['Post-Optimization Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['After optimization, the wing root is not properly contained within the new fuselage'],
                    mui.DialogContentText['The optimization resulted in a fuselage that doesn\'t fully enclose the wing root. Consider adjusting wing position or constraints.']
                ],
                mui.DialogActions[mui.Button(onClick=self.handle_close_wing_new_fus_error, color='error')['Ok']]
            ],
            mui.Dialog(open=self.dialog_open_ht_new_fus_error, onClose=self.handle_close_ht_new_fus_error)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'error.main', 'mb': 1})['🔴'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'error.main', 'pt': 0, 'pb': 1})['Post-Optimization Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['After optimization, the horizontal tail root is not properly contained within the new fuselage'],
                    mui.DialogContentText['The optimization resulted in a fuselage that doesn\'t fully enclose the horizontal tail root. Consider adjusting tail position or constraints.']
                ],
                mui.DialogActions[mui.Button(onClick=self.handle_close_wing_new_fus_error, color='error')['Inspect 3D Model']]
            ],
            mui.Dialog(open=self.dialog_open_vt_new_fus_error, onClose=self.handle_close_vt_new_fus_error)[
                mui.Box(sx={'textAlign': 'center', 'pt': 2})[
                    mui.Typography(variant='h4', sx={'color': 'error.main', 'mb': 1})['🔴'],
                    mui.DialogTitle(sx={'textAlign': 'center', 'color': 'error.main', 'pt': 0, 'pb': 1})['Post-Optimization Error']
                ],
                mui.DialogContent(sx={'textAlign': 'center'})[
                    mui.DialogContentText['After optimization, the vertical tail root is not properly contained within the new fuselage'],
                    mui.DialogContentText['The optimization resulted in a fuselage that doesn\'t fully enclose the vertical tail root. Consider adjusting tail position or constraints.']
                ],
                mui.DialogActions[mui.Button(onClick=self.handle_close_vt_new_fus_error, color='error')['Ok']]
            ],
            mui.Dialog(open=self.busy)[
                layout.Box(orientation="vertical", v_align="center", h_align="center", sx={"p": 4})[
                    mui.CircularProgress(),
                    mui.Typography(variant="h6", sx={"mt": 2})["Running optimization"],
                ]
            ],
        ]

        # Page 0
        if self.page == 0:
            return layout.Split(
                orientation="vertical", height="100%", weights=[0, 1],
            )[
                mui.AppBar(position="static")[
                    mui.Toolbar()[
                        mui.Typography(variant="h6", sx={"flexGrow": 1})[
                            "Area Rule Fuselage Optimizer"
                        ],
                        mui.IconButton(onClick=self.toggle_inputs, sx={"color": "white"})[
                            mui.Icon["menu_open" if self.show_inputs else "menu"]
                        ]
                    ]
                ],
                layout.Box(style={"position": "relative", "height": "100%"})[
                    # --- Floating Edit Button ---
                    (None if self.show_inputs else mui.Fab(
                        color="primary", onClick=self.toggle_inputs,
                        sx={"position": "absolute", "bottom": 24, "left": 24, "zIndex": 1000}
                    )[mui.Icon["edit"]]),

                    layout.Split(
                        height="100%",
                        # --- CLEANED UP COLUMNS: ONLY 3 EXIST NOW ---
                        weights=[0.5, 0, 1] if self.show_inputs else [0, 0, 1]
                    )[
                        # 1. Inputs Panel
                        (inputs if self.show_inputs else mui.Box(sx={"display": "none"})),

                        # 2. Divider
                        (mui.Divider(orientation="vertical") if self.show_inputs else mui.Box(sx={"display": "none"})),

                        # 3. 3D Viewer
                        viewer.Viewer(
                            objects=[
                                AR.aircraft.wings_less_fuselage,
                                AR.aircraft.fuselage,
                                AR.aircraft.vert_tail_less_fuselage,
                                AR.aircraft.hor_tail_less_fuselage,
                                AR.aircraft.constraint_visualizers,
                                PREVIEW_AR.ghost_wings,
                                PREVIEW_AR.ghost_vt,
                                PREVIEW_AR.ghost_ht,
                                PREVIEW_AR.ghost_fuselage,
                                PREVIEW_AR.ghost_constraints
                            ]
                        ),
                    ],
                    *dialogs
                ],
            ]

        # Page 1
        elif self.page == 1:
            # [Keep Page 1 exactly as it was]
            csv_lines = [
                "Metric,Value",
                f"Total initial roughness,{AR.aircraft.optimization.rough_X0:.3e}",
                f"Total optimized roughness,{AR.aircraft.optimization.rough_opt:.3e}",
                f"Roughness change,{AR.aircraft.optimization.rough_reduction:.3e}",
                f"Fuselage initial volume,{AR.aircraft.optimization.Vf_0:.3e}",
                f"Fuselage optimized volume,{AR.aircraft.optimization.Vf_opt:.3e}",
                f"Fuselage volume change,{AR.aircraft.optimization.volume_change:.4f}",
                f"Fuselage initial external area,{AR.aircraft.optimization.A_ext_0:.3e}",
                f"Fuselage final external area,{AR.aircraft.optimization.A_ext_opt:.3e}",
                f"Fuselage external area change,{AR.aircraft.optimization.ext_area_change:.4f}",
            ]
            csv_content = "\n".join(csv_lines)
            csv_url = f"data:text/csv;charset=utf-8,{urllib.parse.quote(csv_content)}"

            return layout.Split(
                orientation="vertical", height="100%", weights=[0, 1],
            )[
                mui.AppBar(position="static")[
                    mui.Toolbar()[
                        mui.Typography(variant="h6", sx={"flexGrow": 1})[
                            "Area Rule Fuselage Optimizer"
                        ],
                        mui.IconButton(onClick=self.toggle_inputs, sx={"color": "white"})[
                            mui.Icon["menu_open" if self.show_inputs else "menu"]
                        ]
                    ]
                ],
                layout.Split(
                    orientation="vertical", height="100%", weights=[1, 0],
                )[
                    layout.Split(
                        orientation="horizontal", height="100%", weights=[0, 1],
                    )[
                        layout.Box(
                            orientation="vertical", style={"padding": "1em", "overflow": "auto", "height": "100%"},
                        )[
                            mui.Typography(variant="h5")["Optimization Results"],
                            mui.Box(sx={"height": "20px"}),
                            mui.TableContainer(component="paper", sx={"border": "1.5px solid #333"})[
                                mui.Table(size="medium")[
                                    mui.TableBody[
                                        mui.TableRow(sx={"height": "50px", "borderBottom": "1px solid #666"})[
                                            mui.TableCell(component="th", scope="row", sx={"fontWeight": "500"})["Total initial roughness:"],
                                            mui.TableCell(align="right", sx={"fontWeight": "500"})[f"{AR.aircraft.optimization.rough_X0:.3e}"],
                                        ],
                                        mui.TableRow(sx={"height": "50px", "borderBottom": "1px solid #666"})[
                                            mui.TableCell(component="th", scope="row", sx={"fontWeight": "500"})["Total optimized roughness:"],
                                            mui.TableCell(align="right", sx={"fontWeight": "500"})[f"{AR.aircraft.optimization.rough_opt:.3e}"],
                                        ],
                                        mui.TableRow(sx={"height": "50px", "borderBottom": "1px solid #666"})[
                                            mui.TableCell(component="th", scope="row", sx={"fontWeight": "500"})["Roughness change:"],
                                            mui.TableCell(align="right", sx={"fontWeight": "500"})[f"{AR.aircraft.optimization.rough_reduction:.4f} %"],
                                        ],
                                        mui.TableRow(sx={"height": "50px", "borderBottom": "1px solid #666"})[
                                            mui.TableCell(component="th", scope="row", sx={"fontWeight": "500"})["Fuselage initial volume:"],
                                            mui.TableCell(align="right", sx={"fontWeight": "500"})[f"{AR.aircraft.optimization.Vf_0:.3e} m³"],
                                        ],
                                        mui.TableRow(sx={"height": "50px", "borderBottom": "1px solid #666"})[
                                            mui.TableCell(component="th", scope="row", sx={"fontWeight": "500"})["Fuselage optimized volume:"],
                                            mui.TableCell(align="right", sx={"fontWeight": "500"})[f"{AR.aircraft.optimization.Vf_opt:.3e} m³"],
                                        ],
                                        mui.TableRow(sx={"height": "50px", "borderBottom": "1px solid #666"})[
                                            mui.TableCell(component="th", scope="row", sx={"fontWeight": "500"})["Fuselage volume change:"],
                                            mui.TableCell(align="right", sx={"fontWeight": "500"})[f"{AR.aircraft.optimization.volume_change:.4f} %"],
                                        ],
                                        mui.TableRow(sx={"height": "50px", "borderBottom": "1px solid #666"})[
                                            mui.TableCell(component="th", scope="row", sx={"fontWeight": "500"})["Fuselage initial external area:"],
                                            mui.TableCell(align="right", sx={"fontWeight": "500"})[f"{AR.aircraft.optimization.A_ext_0:.3e} m²"],
                                        ],
                                        mui.TableRow(sx={"height": "50px", "borderBottom": "1px solid #666"})[
                                            mui.TableCell(component="th", scope="row", sx={"fontWeight": "500"})["Fuselage final external area:"],
                                            mui.TableCell(align="right", sx={"fontWeight": "500"})[f"{AR.aircraft.optimization.A_ext_opt:.3e} m²"],
                                        ],
                                        mui.TableRow(
                                            sx={"height": "50px", "&:last-child td, &:last-child th": {"border": 0}})[
                                            mui.TableCell(component="th", scope="row", sx={"fontWeight": "500"})["Fuselage external area change:"],
                                            mui.TableCell(align="right", sx={"fontWeight": "500"})[f"{AR.aircraft.optimization.ext_area_change:.4f} %"],
                                        ],
                                    ]
                                ]
                            ],
                            mui.Box(sx={"height": "16px"}),
                            layout.Box(h_align="center", sx={"height": "16px"}, style={"overflow": "auto"})[
                                html.a(href=csv_url, download="optimization_results.csv")[
                                    mui.Button(variant="contained", align="centered")["Download Table CSV"]
                                ]
                            ],
                        ],
                        layout.Split(
                            orientation="vertical", height="100%", weights=[0, 1],
                        )[
                            layout.Box(h_align="center", orientation="vertical", style={"padding": "0em", "height": "auto"})[
                                mui.Typography(variant="subtitle1", style={"marginBottom": "0.5em", "marginTop": "0.5em"})["Click on any graph to download it"]
                            ],
                            layout.Box(
                                style={
                                    "display": "grid", "gridTemplateColumns": "repeat(2, 1fr)",
                                    "gridAutoRows": "1fr", "gap": "0.5em", "height": "calc(100% - 1.5em)",
                                }
                            )[
                                *[
                                    html.a(href=img["src"], download=img["filename"], style={"display": "block", "height": "100%", "width": "100%"})[
                                        html.img(src=img["src"], style={"width": "100%", "height": "100%", "objectFit": "contain"})
                                    ]
                                    for img in self.fig_images[:2]
                                ],
                                *(
                                    [
                                        html.a(href=self.fig_images[2]["src"], download=self.fig_images[2]["filename"], style={"display": "block", "height": "100%", "width": "100%", "gridColumn": "1 / -1"})[
                                            html.img(src=self.fig_images[2]["src"], style={"width": "100%", "height": "100%", "objectFit": "contain"})
                                        ]
                                    ]
                                    if len(self.fig_images) > 2 else []
                                ),
                            ],
                        ],
                    ],
                    layout.Box(orientation="horizontal", style={"padding": "0.5em", "justifyContent": "center", "gap": "1em"})[
                        mui.Button(variant="outlined", onClick=lambda _: setattr(self, "page", 0))["Back"],
                        mui.Button(variant="contained" if self.page == 1 else "outlined", onClick=self.switch_to_graphs)["Results"],
                        mui.Button(variant="outlined", onClick=self.switch_to_view3d)["3D View"],
                    ],
                ],
            ]

        # Page 2
        else:
            return layout.Box(
                orientation="vertical", style={"height": "100%"},
            )[
                mui.AppBar(position="static")[
                    mui.Toolbar()[
                        mui.Typography(variant="h6", sx={"flexGrow": 1})[
                            "Area Rule Fuselage Optimizer"
                        ],
                        mui.IconButton(onClick=self.toggle_inputs, sx={"color": "white"})[
                            mui.Icon["menu_open" if self.show_inputs else "menu"]
                        ]
                    ]
                ],
                layout.Box(
                    orientation="horizontal", h_align="center", style={"padding": "0.5em 0.5em", "gap": "2em"},
                )[
                    mui.Button(variant="contained", size="large",
                               onClick=lambda *_: AR.aircraft.optimized_results.download_optimized_fuselage_data())[
                        "Download Optimized Fuselage .txt file"],
                    mui.Button(variant="contained", size="large",
                               onClick=lambda *_: AR.aircraft.optimized_results.step_file_optimized_fuselage())[
                        "Download Optimized Fuselage STEP"],
                    mui.Button(variant="contained", size="large",
                               onClick=lambda *_: AR.aircraft.optimized_results.step_file_optimized_aircraft())[
                        "Download Complete Aircraft STEP"],
                ],
                viewer.Viewer(
                    objects=[
                        AR.aircraft.optimized_results.wings_pair,
                        AR.aircraft.optimized_results.new_fuselage,
                        AR.aircraft.optimized_results.vert_tail,
                        AR.aircraft.optimized_results.hor_tail,
                        AR.aircraft.constraint_visualizers
                    ]
                ),
                layout.Box(orientation="horizontal", style={"padding": "0.5em", "justifyContent": "center", "gap": "1em"})[
                    mui.Button(variant="outlined", onClick=lambda _: setattr(self, "page", 0))["Back"],
                    mui.Button(variant="outlined", onClick=self.switch_to_graphs)["Results"],
                    mui.Button(variant="contained" if self.page == 2 else "outlined", onClick=self.switch_to_view3d)[
                        "3D View"],
                ],
            ]