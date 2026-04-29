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

    def toggle_horizontal(self, event, checked: bool) -> None:
        self.pending_include_hor_tail = checked

    def request_upload_reset(self):
        # Increment reset keys to force file input re-render
        self.reset_key1 += 1
        self.reset_key2 += 1
        self.reset_key3 += 1
        self.reset_key4 += 1

    def render(self) -> NodeType:
        def lifting_surface_section(title, upload, busy, txt, x_offset, z_offset, reset_key, include_title=True):
            """Helper function for lifting surfaces using Sliders for proportional placement"""

            # Get current values as floats for the sliders
            curr_x = float(getattr(self, x_offset))
            curr_z = float(getattr(self, z_offset))

            section = [
                layout.Box(style={"display": "flex", "alignItems": "center", "marginBottom": "1em"})[
                    mui.Button(
                        component="label",
                        variant="outlined",
                        disabled=busy,
                        startIcon=mui.CircularProgress(size=20) if busy else mui.Icon["cloud_upload_icon"],
                    )[
                        f"Upload {title} File",
                        html.input(
                            onChange=upload.get_handler(),
                            type="file",
                            hidden=True,
                            key=f"input-{title.lower()}-{reset_key}"
                        ),
                    ],
                    mui.Typography(variant="body2", sx={"ml": 1})[txt],
                ],

                # --- Longitudinal Position (X) Slider ---
                layout.Box(orientation="vertical", sx={"mb": 2})[
                    mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                        f"{title} X-Position: {int(curr_x * 100)}% of length"
                    ],
                    mui.Slider(
                        value=curr_x,
                        min=0.0,
                        max=1.0,
                        step=0.01,
                        valueLabelDisplay="auto",
                        # Convert back to string for your app.py logic
                        onChangeCommitted=lambda ev, val: setattr(self, x_offset, str(val))
                    )
                ],

                # --- Vertical Position (Z) Slider ---
                layout.Box(orientation="vertical", sx={"mb": 2})[
                    mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                        f"{title} Z-Position: {int(curr_z * 100)}% (relative to radius)"
                    ],
                    mui.Slider(
                        value=curr_z,
                        min=-1.2,  # Allow slightly above/below fuselage
                        max=1.2,
                        step=0.01,
                        valueLabelDisplay="auto",
                        onChangeCommitted=lambda ev, val: setattr(self, z_offset, str(val))
                    )
                ],
                mui.Divider(sx={"my": 1}),
            ]

            if include_title:
                section = [mui.Typography(variant="h6", sx={"mt": 1})[title]] + section

            return section

        def render_constraint_box(i, c):
            return layout.Box(
                key=f"constraint_box_{i}",  # Unique key prevents React from confusing sliders
                style={"border": "1px solid #555", "borderRadius": "4px", "padding": "10px", "marginTop": "10px"}
            )[
                mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                    f"Constraint {i + 1} X-Position: {int(c['x_pct'] * 100)}%"],
                mui.Slider(
                    value=c['x_pct'], min=0.0, max=1.0, step=0.01, valueLabelDisplay="auto",
                    onChangeCommitted=lambda ev, val: self.update_constraint(i, 'x_pct', float(val))
                ),

                mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                    f"Constraint {i + 1} Min Radius: {int(c.get('r_pct', 0.5) * 100)}% of local fuselage"],
                mui.Slider(
                    value=c.get('r_pct', 0.5), min=0.0, max=1.0, step=0.01, valueLabelDisplay="auto",
                    onChangeCommitted=lambda ev, val: self.update_constraint(i, 'r_pct', float(val))
                ),

                layout.Box(h_align="right")[
                    mui.Button(color="error", size="small", onClick=lambda ev: self.remove_constraint(i))["Remove"]
                ]
            ]

        def get_filename(pending_file, busy):
            """Get filename from pending state with upload indicator"""
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
            # Fuselage first (without offsets)
            mui.Typography(variant="h6")["Fuselage"],
            layout.Box(style={"display": "flex", "alignItems": "center"})[
                mui.Button(
                    component="label",
                    variant="outlined",
                    disabled=busy[3],
                    startIcon=mui.CircularProgress(size=20) if busy[3] else mui.Icon["cloud_upload_icon"],
                )[
                    "Upload Fuselage File",
                    html.input(
                        onChange=self.upload4.get_handler(),
                        type="file",
                        hidden=True,
                        key=f"input-fuselage-{self.reset_key4}"
                    ),
                ],
                filenames[3],
            ],

            layout.Box(orientation="vertical", gap="1.5em", style={"marginTop": "1em", "padding": "0 10px"})[
                # --- NOSE LENGTH ---
                layout.Box(orientation="vertical")[
                    mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                        f"Nose Length: {self.pending_nose_length} m"],
                    mui.Slider(
                        value=float(self.pending_nose_length),
                        min=5.0,
                        max=25.0,
                        step=0.1,
                        valueLabelDisplay="auto",
                        onChangeCommitted=lambda ev, val: setattr(self, "pending_nose_length", str(val))
                    )
                ],

                    # --- MAIN BODY LENGTH ---
                layout.Box(orientation="vertical")[
                    mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                        f"Main Body Length: {self.pending_main_body_length} m"],
                    mui.Slider(
                        value=float(self.pending_main_body_length),
                        min=10.0,
                        max=60.0,
                        step=0.5,
                        valueLabelDisplay="auto",
                        onChangeCommitted=lambda ev, val: setattr(self, "pending_main_body_length", str(val))
                    )
                ],

                    # --- TAIL LENGTH ---
                layout.Box(orientation="vertical")[
                    mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                        f"Tail Length: {self.pending_tail_length} m"],
                    mui.Slider(
                        value=float(self.pending_tail_length),
                        min=5.0,
                        max=30.0,
                        step=0.1,
                        valueLabelDisplay="auto",
                        onChangeCommitted=lambda ev, val: setattr(self, "pending_tail_length", str(val))
                    )
                ],

                    # --- FUSELAGE RADIUS ---
                layout.Box(orientation="vertical")[
                    mui.Typography(variant="caption", sx={"color": "text.secondary"})[
                        f"Fuselage Radius: {self.pending_fuselage_radius} m"],
                    mui.Slider(
                        value=float(self.pending_fuselage_radius),
                        min=1.0, max=5.0, step=0.01, valueLabelDisplay="auto",
                        onChangeCommitted=lambda ev, val: setattr(self, "pending_fuselage_radius", str(val))
                    )
                ],

                mui.Divider(sx={"my": 1}),

                    # --- USER DEFINED CONSTRAINTS ---
                mui.Typography(variant="subtitle2")["Minimum Radius Constraints"],
                mui.Button(variant="outlined", size="small", onClick=self.add_constraint)["+ Add Constraint"],

                *[render_constraint_box(i, c) for i, c in enumerate(self.pending_user_constraints)]
            ],

            mui.Divider(),

            # Wing
            *lifting_surface_section(
                "Wing", self.upload1, busy[0], filenames[0],
                "pending_x_offs_wings", "pending_z_offs_wings", self.reset_key1
            ),

            # Vertical Tail
            *lifting_surface_section(
                "Vertical Tail", self.upload2, busy[1], filenames[1],
                "pending_x_offs_vert_tail", "pending_z_offs_vert_tail", self.reset_key2
            ),

            # Horizontal Tail
            layout.Box(style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"})[
                mui.Typography(variant="h6")["Horizontal Tail"],
                mui.Checkbox(
                    checked=self.pending_include_hor_tail,
                    onChange=self.toggle_horizontal,
                ),
            ],
            # Conditionally show horizontal tail section
            *(lifting_surface_section(
                "Horizontal Tail", self.upload3, busy[2], filenames[2],
                "pending_x_offs_tail", "pending_z_offs_tail", self.reset_key3,
                include_title=False
            ) if self.pending_include_hor_tail else [])
        ]