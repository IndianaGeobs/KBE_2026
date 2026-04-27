import os
from parapy.webgui import layout, html, mui
from parapy.webgui.core import Component, NodeType, FileUpload, Prop, State

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

    pending_include_hor_tail = State(AR.include_hor_tail)

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
            """Helper function for lifting surfaces with optional title"""
            section = [
                layout.Box(style={"display": "flex", "alignItems": "center"})[
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
                    txt,
                ],
                mui.TextField(
                    label="x-Offset [m]",
                    type="number",
                    value=getattr(self, x_offset),
                    onChange=lambda ev: setattr(self, x_offset, ev.target.value),
                ),
                mui.TextField(
                    label="z-Offset [m]",
                    type="number",
                    value=getattr(self, z_offset),
                    onChange=lambda ev: setattr(self, z_offset, ev.target.value),
                ),
                mui.Divider(),
            ]

            if include_title:
                section = [mui.Typography(variant="h6")[title]] + section

            return section

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