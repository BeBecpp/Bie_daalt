"""Boilerplate shared by every scene builder: CLI, render setup, world,
fonts, title overlay scene, compositor, save and render."""
import os

import bpy

from . import common as C
from . import sets as S
from .overlay import TitleScene, build_compositor, install_counter_handler


class Shot:
    def __init__(self, number, name, default_duration, extra=None, samples_preview=20,
                 samples_final=128, world_hex="#11110F", world_strength=0.3):
        self.number = number
        self.args = C.parse_args(extra)
        self.D = self.args.duration or default_duration
        self.s = self.D / default_duration
        self.n_frames = int(round(self.D * C.FPS))
        self.scene = C.reset_scene(f"S{number}_{name}")
        C.setup_render(self.scene, self.args, self.n_frames, samples_preview, samples_final)
        w = bpy.data.worlds.new(f"S{number}_World")
        w.use_nodes = True
        bg = w.node_tree.nodes["Background"]
        bg.inputs["Color"].default_value = C.hex_rgba(world_hex)
        bg.inputs["Strength"].default_value = world_strength
        self.scene.world = w
        self.fonts = S.fonts()
        self.titles = TitleScene(self.scene, f"S{number}_Titles")
        self.fps = C.FPS * self.s

    # beat in seconds at the default duration -> frame
    def t(self, sec):
        return int(round(C.sec(sec * self.s)))

    def camera(self, name, lens, fstop=None, collection=None):
        cd = bpy.data.cameras.new(name)
        cd.lens, cd.sensor_width, cd.clip_start, cd.clip_end = lens, 36, 0.01, 5000
        cam = C.link(bpy.data.objects.new(name, cd), collection)
        aim = C.empty(f"{name}_Aim", (0, 0, 0), collection)
        tt = cam.constraints.new("TRACK_TO")
        tt.target = aim
        tt.track_axis, tt.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
        if fstop:
            cd.dof.use_dof = True
            cd.dof.aperture_fstop = fstop
            cd.dof.focus_object = aim
        return cam, aim

    def move(self, cam, aim, keys):
        """keys: [(frame, cam_loc, aim_loc), ...] with smooth interpolation."""
        for f, c, a in keys:
            C.key(cam, "location", f, tuple(c))
            C.key(aim, "location", f, tuple(a))
        for idb in (cam, aim):
            C.set_interpolation(idb, "BEZIER", handle="AUTO_CLAMPED")

    def cut(self, name, frame, cam):
        m = self.scene.timeline_markers.new(name, frame=int(frame))
        m.camera = cam
        if frame <= 1:
            self.scene.camera = cam

    def label(self, text="Уран сайхны сэргээн дүрслэл", f_in=None, f_out=None):
        ts = self.titles
        lab = ts.text("ReconLabel", text, self.fonts["sans_regular"], 0.27, (-7.25, -4.05, 0),
                      color="#F1E4CC", strength=1.0, align_x="LEFT", halo=0.0, plate=0.85)
        f_in = f_in or self.t(0.5)
        if f_out:
            TitleScene.fade(lab, f_in, f_in + 0.8 * self.fps, f_out - 0.5 * self.fps, f_out, peak=0.9)
        else:
            TitleScene.fade(lab, f_in, f_in + 0.8 * self.fps, peak=0.9)
        return lab

    def card(self, name, body, size, y, f_in, f_out=None, font="serif", color="#F1E4CC", strength=1.1,
             spacing=1.0, x=0.0, align="CENTER", halo=0.45, plate=0.0):
        o = self.titles.text(name, body, self.fonts[font], size, (x, y, 0), color=color, strength=strength,
                             spacing=spacing, align_x=align, halo=halo, plate=plate)
        f_out = f_out or self.n_frames + 50
        TitleScene.fade(o, f_in, f_in + 0.6 * self.fps, f_out - 0.5 * self.fps, f_out)
        return o

    def finish(self, fade_in=(1, 30), counters=False):
        if counters:
            install_counter_handler()
        build_compositor(self.scene, self.titles.scene, fade_in=fade_in)
        a = self.args
        if not a.no_save:
            C.save_blend(os.path.join(C.SCENES_DIR, f"scene{self.number}.blend"))
        out = a.out or os.path.join(C.OUTPUT_DIR, f"scene{self.number}_{a.quality}_frames")
        if a.stills:
            C.render_frames(self.scene, out, stills=[int(x) for x in a.stills.split(",")])
        elif a.render:
            C.render_frames(self.scene, out, frames=C.frame_range_from_arg(a.frames, self.n_frames))
