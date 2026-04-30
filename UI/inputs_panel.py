import os
from parapy.webgui import layout, html, mui
from parapy.webgui.core import Component, NodeType, FileUpload, Prop, State, update

from area_rule import AR


class InputsPanel(Component):
    """InputsPanel: holds pending files and pending numeric strings"""
    on_upload1 = Prop()
    on_upload2 = Prop()
    on_upload3 = Prop()
    on_upload4 = Prop()

    # --- NEW PROPS FOR BUTTONS ---
    on_close = Prop()
    on_apply = Prop()
    is_applying = Prop()
    on_optimize = Prop()
    is_busy = Prop()
    # -----------------------------

    show_horizontal = State(True)

    # FileUpload components
    upload1 = FileUpload("Wing")
    upload2 = FileUpload("Vertical Tail")
    upload3 = FileUpload("Horizontal Tail")
    upload4 = FileUpload("Fuselage")

    pending_wing_file = State(AR.wing_file)
    pending_vert_tail_file = State(AR.vert_tail_file)
    pending_hor_tail_file = State(AR.hor_tail_file)
    pending_fuselage_file = State(AR.fuselage_file)

    pending_x_offs_wings = State(str(AR.x_offs_wings))
    pending_z_offs_wings = State(str(AR.z_offs_wings))
    pending_x_offs_tail = State(str(AR.x_offs_tail))
    pending_z_offs_tail = State(str(AR.z_offs_tail))
    pending_x_offs_vert_tail = State(str(AR.x_offs_vert_tail))
    pending_z_offs_vert_tail = State(str(AR.z_offs_vert_tail))

    pending_wing_dihedral = State("5.0")
    pending_wing_root_chord = State("0.2")
    pending_wing_sections = State([
        {"span": 0.40, "root_chord": 0.2, "tip_chord": 0.05, "sweep": 40.0}
    ])

    pending_nose_length = State("12.6")
    pending_main_body_length = State("31.5")
    pending_tail_length = State("18.9")
    pending_fuselage_radius = State("2.829")

    pending_include_hor_tail = State(AR.include_hor_tail)

    pending_user_constraints = State([])

    # Reset keys to force file input re-render
    reset_key1 = State(0)
    reset_key2 = State(0)
    reset_key3 = State(0)
    reset_key4 = State(0)

    @upload1.on_complete
    def _on_wing(self, file):
        fname = getattr(file["0"], "filename", "wing.txt")
        self._handle_upload(file, fname, "pending_wing_file", "on_upload1")

    @upload2.on_complete
    def _on_vert_tail(self, file):
        fname = getattr(file["0"], "filename", "vert_tail.txt")
        self._handle_upload(file, fname, "pending_vert_tail_file", "on_upload2")

    @upload3.on_complete
    def _on_horiz_tail(self, file):
        fname = getattr(file["0"], "filename", "hor_tail.txt")
        self._handle_upload(file, fname, "pending_hor_tail_file", "on_upload3")

    @upload4.on_complete
    def _on_fuselage(self, file):
        fname = getattr(file["0"], "filename", "fuselage.txt")
        self._handle_upload(file, fname, "pending_fuselage_file", "on_upload4", binary=True)

    def _handle_upload(self, file, filename, state_var, callback, binary=False):
        new_path = os.path.join(os.path.dirname(__file__), filename)
        data = file["0"].read()
        mode = "wb" if binary else "w"
        encoding = None if binary else "utf-8"

        with open(new_path, mode, encoding=encoding) as f:
            f.write(data if binary else data.decode("utf-8"))

        setattr(self, state_var, new_path)
        getattr(self, callback)(new_path)

    # Constraints helper functions
    def add_constraint(self, *args):
        new_list = list(self.pending_user_constraints)
        new_list.append({"x_pct": 0.5, "r_pct": 0.5})
        self.pending_user_constraints = new_list
        AR.user_constraints = new_list
        update()

    def remove_constraint(self, idx):
        new_list = list(self.pending_user_constraints)
        new_list.pop(idx)
        self.pending_user_constraints = new_list
        AR.user_constraints = new_list
        update()

    def update_constraint(self, idx, key, val):
        new_list = list(self.pending_user_constraints)
        new_list[idx] = dict(new_list[idx])
        new_list[idx][key] = val
        self.pending_user_constraints = new_list
        AR.user_constraints = new_list
        update()

    # Wings helper functions
    def add_wing_section(self, *args):
        sections = list(self.pending_wing_sections)
        if len(sections) < 3:
            last_tip = sections[-1]["tip_chord"]
            # Adding section with small ratios instead of massive meters
            sections.append({"span": 0.06, "root_chord": last_tip, "tip_chord": 0.015, "sweep": 30.0})
            self.pending_wing_sections = sections
            update()

    def remove_wing_section(self, *args):
        sections = list(self.pending_wing_sections)
        if len(sections) > 1:
            sections.pop()
            self.pending_wing_sections = sections
            update()

    def update_wing_section(self, idx, key, val):
        sections = list(self.pending_wing_sections)
        sections[idx] = dict(sections[idx])
        sections[idx][key] = val

        if key == "tip_chord" and idx < len(sections) - 1:
            sections[idx + 1] = dict(sections[idx + 1])
            sections[idx + 1]["root_chord"] = val
        elif key == "root_chord" and idx > 0:
            sections[idx - 1] = dict(sections[idx - 1])
            sections[idx - 1]["tip_chord"] = val
        elif key == "root_chord" and idx == 0:
            self.pending_wing_root_chord = str(val)

        self.pending_wing_sections = sections
        update()

    def toggle_horizontal(self, event, checked: bool) -> None:
        self.pending_include_hor_tail = checked

    def request_upload_reset(self):
        self.reset_key1 += 1
        self.reset_key2 += 1
        self.reset_key3 += 1
        self.reset_key4 += 1

    def render(self) -> NodeType:
        try:
            total_length = float(self.pending_nose_length) + float(self.pending_main_body_length) + float(
                self.pending_tail_length)
        except ValueError:
            total_length = 63.0

        max_chord_limit = round(0.60 * total_length, 2)

        def lifting_surface_section(title, upload, busy, txt, x_offset, z_offset, reset_key, include_title=True):
            curr_x = float(getattr(self, x_offset))
            curr_z = float(getattr(self, z_offset))

            section = [
                layout.Box(style={"display": "flex", "alignItems": "center", "marginBottom": "1em"})[
                    mui.Button(
                        component="label", variant="outlined", disabled=busy,
                        startIcon=mui.CircularProgress(size=20) if busy else mui.Icon["cloud_upload_icon"],
                    )[
                        f"Upload {title} File",
                        html.input(onChange=upload.get_handler(), type="file", hidden=True,
                                   key=f"input-{title.lower()}-{reset_key}"),
                    ],
                    mui.Typography(variant="body2", sx={"ml": 1})[txt],
                ],
                layout.Box(orientation="vertical", sx={"mb": 2})[
                    mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                        f"{title} X-Position: {int(curr_x * 100)}% of length"],
                    mui.Slider(value=curr_x, min=0.0, max=1.0, step=0.01, valueLabelDisplay="auto",
                               onChangeCommitted=lambda ev, val: setattr(self, x_offset, str(val)))
                ],
                layout.Box(orientation="vertical", sx={"mb": 2})[
                    mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                        f"{title} Z-Position: {int(curr_z * 100)}% (relative to radius)"],
                    mui.Slider(value=curr_z, min=-1.2, max=1.2, step=0.01, valueLabelDisplay="auto",
                               onChangeCommitted=lambda ev, val: setattr(self, z_offset, str(val)))
                ],
                mui.Divider(sx={"my": 1}),
            ]
            if include_title:
                section = [mui.Typography(variant="h6", sx={"mt": 1})[title]] + section
            return section

        def render_constraint_box(i, c):
            return layout.Box(
                key=f"constraint_box_{i}",
                style={"border": "1px solid #555", "borderRadius": "4px", "padding": "10px", "marginTop": "10px"}
            )[
                mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                    f"Constraint {i + 1} X-Position: {int(c['x_pct'] * 100)}%"],
                mui.Slider(value=c['x_pct'], min=0.0, max=1.0, step=0.01, valueLabelDisplay="auto",
                           onChangeCommitted=lambda ev, val: self.update_constraint(i, 'x_pct', float(val))),
                mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                    f"Constraint {i + 1} Min Radius: {int(c.get('r_pct', 0.5) * 100)}% of local fuselage"],
                mui.Slider(value=c.get('r_pct', 0.5), min=0.0, max=1.0, step=0.01, valueLabelDisplay="auto",
                           onChangeCommitted=lambda ev, val: self.update_constraint(i, 'r_pct', float(val))),
                layout.Box(h_align="right")[
                    mui.Button(color="error", size="small", onClick=lambda ev: self.remove_constraint(i))["Remove"]]
            ]

        def get_filename(pending_file, busy):
            pending = getattr(self, pending_file)
            name = os.path.basename(pending) if pending else ""
            return f"{name} (uploading...)" if busy else name

        busy = [
            self.upload1.status not in ("Idle", "Complete"),
            self.upload2.status not in ("Idle", "Complete"),
            self.upload3.status not in ("Idle", "Complete"),
            self.upload4.status not in ("Idle", "Complete"),
        ]

        filenames = [
            get_filename("pending_wing_file", busy[0]),
            get_filename("pending_vert_tail_file", busy[1]),
            get_filename("pending_hor_tail_file", busy[2]),
            get_filename("pending_fuselage_file", busy[3]),
        ]

        return layout.Box(orientation="vertical", gap="1em", style={"padding": "1em"})[

            # --- HEADER WITH APPLY & CLOSE BUTTONS ---
            layout.Box(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
                              "marginBottom": "-10px"})[
                mui.Typography(variant="h5")["Parameters"],

                    # Increased gap from 10px to 15px
                layout.Box(style={"display": "flex", "gap": "15px", "alignItems": "center"})[
                    mui.Button(
                        variant="contained",
                        size="small",
                        onClick=self.on_apply,
                        disabled=self.is_applying,
                        sx={"padding": "6px 20px"}
                    )[
                        layout.Box(orientation="horizontal", gap="0.5em", h_align="center")[
                            mui.CircularProgress(size=16, sx={"color": "white"}) if self.is_applying else None,
                            "Apply"
                        ]
                    ],
                    mui.IconButton(onClick=lambda ev: self.on_close(), size="small")[
                        mui.Icon["close"]
                    ]
                ]
            ],
            mui.Divider(),
                # ----------------------------------------

            mui.Typography(variant="h6")["Fuselage"],
            layout.Box(style={"display": "flex", "alignItems": "center"})[
                mui.Button(
                    component="label", variant="outlined", disabled=busy[3],
                    startIcon=mui.CircularProgress(size=20) if busy[3] else mui.Icon["cloud_upload_icon"],
                )[
                    "Upload Fuselage File",
                    html.input(onChange=self.upload4.get_handler(), type="file", hidden=True,
                               key=f"input-fuselage-{self.reset_key4}"),
                ],
                filenames[3],
            ],

            layout.Box(orientation="vertical", gap="1.5em", style={"marginTop": "1em", "padding": "0 10px"})[
                layout.Box(orientation="vertical")[
                    mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                        f"Nose Length: {self.pending_nose_length} m"],
                    mui.Slider(value=float(self.pending_nose_length), min=5.0, max=25.0, step=0.1,
                               valueLabelDisplay="auto",
                               onChangeCommitted=lambda ev, val: setattr(self, "pending_nose_length", str(val)))
                ],
                layout.Box(orientation="vertical")[
                    mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                        f"Main Body Length: {self.pending_main_body_length} m"],
                    mui.Slider(value=float(self.pending_main_body_length), min=10.0, max=60.0, step=0.5,
                               valueLabelDisplay="auto",
                               onChangeCommitted=lambda ev, val: setattr(self, "pending_main_body_length", str(val)))
                ],
                layout.Box(orientation="vertical")[
                    mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                        f"Tail Length: {self.pending_tail_length} m"],
                    mui.Slider(value=float(self.pending_tail_length), min=5.0, max=30.0, step=0.1,
                               valueLabelDisplay="auto",
                               onChangeCommitted=lambda ev, val: setattr(self, "pending_tail_length", str(val)))
                ],
                layout.Box(orientation="vertical")[
                    mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                        f"Fuselage Radius: {self.pending_fuselage_radius} m"],
                    mui.Slider(value=float(self.pending_fuselage_radius), min=1.0, max=5.0, step=0.01,
                               valueLabelDisplay="auto",
                               onChangeCommitted=lambda ev, val: setattr(self, "pending_fuselage_radius", str(val)))
                ],
                mui.Divider(sx={"my": 1}),
                mui.Typography(variant="subtitle2")["Minimum Radius Constraints"],
                mui.Button(variant="outlined", size="small", onClick=self.add_constraint)["+ Add Constraint"],
                *[render_constraint_box(i, c) for i, c in enumerate(self.pending_user_constraints)]
            ],

            mui.Divider(),
            mui.Typography(variant="h6", sx={"mt": 1})["Main Wing"],

            layout.Box(style={"display": "flex", "alignItems": "center", "marginBottom": "1em"})[
                mui.Button(component="label", variant="outlined", disabled=busy[0])[
                    "Upload 2D Airfoil Data (.txt)",
                    html.input(onChange=self.upload1.get_handler(), type="file", hidden=True,
                               key=f"input-wing-{self.reset_key1}"),
                ],
                mui.Typography(variant="body2", sx={"ml": 1})[filenames[0]],
            ],

            layout.Box(orientation="vertical", sx={"mb": 2})[
                mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                    f"Wing X-Position: {int(float(self.pending_x_offs_wings) * 100)}% of length"],
                mui.Slider(value=float(self.pending_x_offs_wings), min=0.0, max=1.0, step=0.01,
                           valueLabelDisplay="auto",
                           onChangeCommitted=lambda ev, val: setattr(self, "pending_x_offs_wings", str(val)))
            ],
            layout.Box(orientation="vertical", sx={"mb": 2})[
                mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                    f"Wing Z-Position: {int(float(self.pending_z_offs_wings) * 100)}% (relative)"],
                mui.Slider(value=float(self.pending_z_offs_wings), min=-1.2, max=1.2, step=0.01,
                           valueLabelDisplay="auto",
                           onChangeCommitted=lambda ev, val: setattr(self, "pending_z_offs_wings", str(val)))
            ],

            mui.Divider(sx={"my": 1}),
            mui.Typography(variant="subtitle2")["Wing Geometry (Max 3 Sections)"],

            layout.Box(orientation="vertical", sx={"mt": 1, "padding": "0 10px"})[
                mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                    f"Global Dihedral: {self.pending_wing_dihedral}°"],
                mui.Slider(value=float(self.pending_wing_dihedral), min=-10.0, max=15.0, step=0.5,
                           valueLabelDisplay="auto",
                           onChangeCommitted=lambda ev, val: setattr(self, "pending_wing_dihedral", str(val))),
            ],

            layout.Box(orientation="vertical", style={"padding": "0 10px"})[
                *[
                    layout.Box(key=f"wing_sec_{i}",
                               style={"border": "1px solid #555", "borderRadius": "4px", "padding": "10px",
                                      "marginTop": "10px"})[
                        mui.Typography(variant="subtitle2", sx={"mb": 1})[f"Section {i + 1}"],

                        mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                            f"Root Chord: {int(sec['root_chord'] * 100)}% of Fuselage"],
                        mui.Slider(value=sec['root_chord'], min=0.01, max=0.5, step=0.01,
                                   valueLabelDisplay="auto",
                                   onChangeCommitted=lambda ev, val, idx=i: self.update_wing_section(idx, 'root_chord',
                                                                                                     float(val))),

                        mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                            f"Span: {int(sec['span'] * 100)}% of Fuselage"],
                        mui.Slider(value=sec['span'], min=0.01, max=0.5, step=0.01, valueLabelDisplay="auto",
                                   onChangeCommitted=lambda ev, val, idx=i: self.update_wing_section(idx, 'span',
                                                                                                     float(val))),

                        mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                            f"Tip Chord: {int(sec['tip_chord'] * 100)}% of Fuselage"],
                        mui.Slider(value=sec['tip_chord'], min=0.01, max=0.5, step=0.01,
                                   valueLabelDisplay="auto",
                                   onChangeCommitted=lambda ev, val, idx=i: self.update_wing_section(idx, 'tip_chord',
                                                                                                     float(val))),

                        mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                            f"LE Sweep Angle: {sec['sweep']}°"],
                        mui.Slider(value=sec['sweep'], min=-20.0, max=60.0, step=0.5, valueLabelDisplay="auto",
                                   onChangeCommitted=lambda ev, val, idx=i: self.update_wing_section(idx, 'sweep',
                                                                                                     float(val))),
                    ] for i, sec in enumerate(self.pending_wing_sections)
                ],
                layout.Box(style={"display": "flex", "gap": "10px", "marginTop": "10px"})[
                    mui.Button(variant="outlined", size="small", onClick=self.add_wing_section,
                               disabled=len(self.pending_wing_sections) >= 3)["+ Add Section"],
                    mui.Button(variant="outlined", size="small", color="error", onClick=self.remove_wing_section,
                               disabled=len(self.pending_wing_sections) <= 1)["- Remove Section"],
                ],
            ],
            mui.Divider(sx={"my": 2}),

            *lifting_surface_section("Vertical Tail", self.upload2, busy[1], filenames[1], "pending_x_offs_vert_tail",
                                     "pending_z_offs_vert_tail", self.reset_key2),

            layout.Box(style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"})[
                mui.Typography(variant="h6")["Horizontal Tail"],
                mui.Checkbox(checked=self.pending_include_hor_tail, onChange=self.toggle_horizontal),
            ],
            *(lifting_surface_section("Horizontal Tail", self.upload3, busy[2], filenames[2], "pending_x_offs_tail",
                                      "pending_z_offs_tail", self.reset_key3,
                                      include_title=False) if self.pending_include_hor_tail else []),

                # --- FOOTER WITH BIG OPTIMIZE BUTTON ---
            mui.Divider(sx={"my": 3}),
            mui.Button(
                variant="contained", color="success", size="large", fullWidth=True,
                onClick=self.on_optimize, disabled=self.is_busy
            )[
                layout.Box(orientation="horizontal", gap="0.5em", h_align="center")[
                    mui.CircularProgress(size=20, sx={"color": "white"}) if self.is_busy else None,
                    "Optimize Geometry"
                ]
            ]
            # ---------------------------------------
        ]