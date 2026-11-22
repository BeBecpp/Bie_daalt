"""SCENE 01 — THE MOMENT (proof of concept)

1924-11-26, 16:17. Darkness -> a desk lamp warms up over an aged manuscript
(abstract, illegible column script = labelled artistic reconstruction) ->
a macro camera glides across the ink, dust drifting through the light ->
rack focus to a brass pocket watch whose second hand reaches 12 as the
minute hand lands on 17 -> modern Mongolian title card.

Run (from the project root):
    blender -b --factory-startup --python scripts/build_scene01.py -- --stills 1,48,96,132,192
    blender -b --factory-startup --python scripts/build_scene01.py -- --render
    blender -b --factory-startup --python scripts/build_scene01.py -- --quality final --engine eevee --render
    blender -b --factory-startup --python scripts/build_scene01.py -- --duration 17 --render   # stretch to VO

All beats are expressed relative to --duration, so the shot can be
retimed to the real narration length without editing keyframes by hand.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import common as C          # noqa: E402
from lib import materials as M       # noqa: E402
from lib import props as P           # noqa: E402
from lib import textures as T        # noqa: E402
from lib.overlay import TitleScene, build_compositor  # noqa: E402

DEFAULT_DURATION = 8.0


def extra_args(p):
    p.add_argument("--manuscript-image", default=None,
                   help="rights-cleared scan to use instead of the procedural abstract manuscript")


def main():
    args = C.parse_args(extra_args)
    D = args.duration or DEFAULT_DURATION
    n_frames = int(round(D * C.FPS))
    scene = C.reset_scene("S01_TheMoment")
    C.setup_render(scene, args, n_frames, samples_preview=28, samples_final=128)

    # ---- beats (seconds). Everything scales with D. -------------------------
    s = D / DEFAULT_DURATION
    B = {
        "light_on": 0.15 * s, "light_full": 1.6 * s,
        "glide_mid": 2.7 * s, "turn": 4.3 * s,
        "hit": 5.5 * s,                       # clock reads exactly 16:17:00
        "title": 5.75 * s, "end": D,
    }
    F = {k: C.sec(v) for k, v in B.items()}
    F["end"] = n_frames

    # ---- world ----------------------------------------------------------------
    world = bpy.data.worlds.new("S01_World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = C.hex_rgba("#11110F")
    bg.inputs["Strength"].default_value = 0.35
    scene.world = world

    set_col = C.new_collection("Set")
    hero_col = C.new_collection("Hero")
    fx_col = C.new_collection("FX")
    light_col = C.new_collection("Lights")

    # ---- desk + room ---------------------------------------------------------
    desk = P.box("Desk", (2.4, 1.6, 0.04), (0, 0.3, -0.02), set_col, M.wood(), bevel=0)
    wall_mat = M.flat("Plaster", "#2a2520", roughness=0.9)
    wall = P.box("Wall", (4.0, 0.05, 2.0), (0, 1.5, 0.9), set_col, wall_mat, bevel=0)

    # ---- manuscript ------------------------------------------------------------
    tex_w = 2048 if args.quality == "preview" else 4096
    if args.manuscript_image:
        albedo, ink = os.path.abspath(args.manuscript_image), None
    else:
        albedo, ink = T.make_manuscript_textures(C.GEN_TEX_DIR, width=tex_w)
    paper = P.parchment_sheet("Manuscript", mat=M.parchment(albedo, ink), collection=hero_col)
    paper.location = (-0.04, 0.03, 0.0)
    paper.rotation_euler.z = math.radians(4)
    # an older folded sheet half under it, for depth layering
    paper2 = P.parchment_sheet("Manuscript_Under", size=(0.21, 0.30), res=(60, 86),
                               mat=M.parchment(albedo, ink), collection=set_col, seed=21, curl=0.6)
    paper2.location = (0.21, 0.22, -0.0006)
    paper2.rotation_euler.z = math.radians(-17)

    # crimson silk ribbon: the film's recurring red motif (symbolic only)
    P.ribbon("RedRibbon", [(-0.10, 0.12, 0.0016), (-0.16, 0.02, 0.0004), (-0.20, -0.10, 0.0004),
                           (-0.17, -0.21, 0.0006), (-0.09, -0.29, 0.0004), (0.02, -0.33, 0.0004)],
             width=0.014, collection=set_col, mat=M.satin("CrimsonSilk", "#782E2F"), twist=0.25)

    # ---- pocket watch -------------------------------------------------------
    fonts = {"serif": C.load_font("NotoSerif-SemiBold.ttf"),
             "serif_regular": C.load_font("NotoSerif-Regular.ttf"),
             "sans": C.load_font("NotoSans-Medium.ttf"),
             "sans_regular": C.load_font("NotoSans-Regular.ttf")}
    W = Vector((0.17, -0.10, 0.0))
    watch = P.pocket_watch("Watch", fonts, collection=hero_col)
    watch["root"].location = W
    watch["root"].rotation_euler.z = math.radians(-8)
    brass = bpy.data.materials["Brass"]
    a = math.radians(-8)
    def wp(x, y, z=0.0006):  # watch-local -> world (only z-rotation)
        return (W.x + x * math.cos(a) - y * math.sin(a), W.y + x * math.sin(a) + y * math.cos(a), z)
    P.chain("WatchChain", [wp(0, 0.044), wp(0.012, 0.07), wp(0.05, 0.085), wp(0.085, 0.06),
                           wp(0.12, 0.05), wp(0.17, 0.08), wp(0.26, 0.12)],
            collection=hero_col, mat=brass)

    # ---- background dressing (out of focus; gives depth and bokeh) ------------
    leather = [M.flat("LeatherOx", "#3b1612", 0.55, coat=0.2), M.flat("LeatherBrown", "#3a2615", 0.6, coat=0.2),
               M.flat("LeatherDark", "#1f1a14", 0.5, coat=0.2)]
    for i, (sz, rz) in enumerate((((0.24, 0.17, 0.035), 0.06), ((0.22, 0.16, 0.03), -0.05),
                                  ((0.20, 0.15, 0.028), 0.14))):
        P.box(f"Book{i}", sz, (0.02 + 0.01 * i, 0.50, 0.0175 + i * 0.033), set_col, leather[i], rot_z=rz)
    P.cylinder("Inkwell", 0.026, 0.05, (-0.27, 0.27, 0.025), set_col,
               M.glass("InkwellGlass", 0.05))
    P.cylinder("InkwellInk", 0.022, 0.03, (-0.27, 0.27, 0.016), set_col,
               M.flat("Ink", "#050404", 0.05))
    P.cylinder("InkwellLid", 0.017, 0.012, (-0.27, 0.27, 0.056), set_col, brass)
    # distant practical lamps -> soft bokeh in the background
    for i, (x, y, z) in enumerate(((0.75, 1.3, 0.42), (0.95, 1.35, 0.30), (-0.85, 1.4, 0.5))):
        b = P.cylinder(f"Practical{i}", 0.012, 0.02, (x, y, z), set_col,
                       M.emission(f"PracticalGlow{i}", "#ffb36b", 40.0), segments=16)

    # ---- lights (animated) ------------------------------------------------------
    key_target = C.empty("KeyTarget", (0.05, -0.04, 0.0), light_col)
    key_data = bpy.data.lights.new("KeyLamp", "SPOT")
    key_data.color = C.kelvin_rgb(3700)
    key_data.spot_size = math.radians(55)
    key_data.spot_blend = 0.65
    key_data.shadow_soft_size = 0.035
    key_light = C.link(bpy.data.objects.new("KeyLamp", key_data), light_col)
    tr = key_light.constraints.new("TRACK_TO")
    tr.target = key_target
    tr.track_axis, tr.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    # lamp warms up, then breathes very slightly; its position drifts so shadows travel
    for f, e in ((1, 0.0), (F["light_on"], 0.0), (F["light_full"], 95.0), (F["hit"], 105.0), (F["end"], 100.0)):
        C.key(key_data, "energy", f, e)
    for f, loc in ((1, (-0.62, 0.30, 0.42)), (F["end"], (-0.52, 0.36, 0.44))):
        C.key(key_light, "location", f, loc)

    fill = bpy.data.lights.new("WindowFill", "AREA")
    fill.shape = "RECTANGLE"
    fill.size, fill.size_y = 1.2, 0.8
    fill.color = (0.70, 0.80, 1.0)
    fill_obj = C.link(bpy.data.objects.new("WindowFill", fill), light_col)
    fill_obj.location = (1.1, 0.4, 0.9)
    C.look_at(fill_obj, (0.0, 0.0, 0.0))
    for f, e in ((1, 0.0), (F["light_full"], 9.0), (F["end"], 9.0)):
        C.key(fill, "energy", f, e)

    rim = bpy.data.lights.new("RimGlint", "AREA")
    rim.size = 0.08
    rim.color = C.kelvin_rgb(3600)
    rim_obj = C.link(bpy.data.objects.new("RimGlint", rim), light_col)
    rim_obj.location = (0.30, 0.18, 0.10)
    C.look_at(rim_obj, tuple(W))
    for f, e in ((1, 0.0), (F["turn"], 0.6), (F["hit"], 2.6), (F["end"], 2.2)):
        C.key(rim, "energy", f, e)

    # ---- camera ------------------------------------------------------------
    cam_data = bpy.data.cameras.new("S01_Cam")
    cam_data.lens = 65
    cam_data.sensor_width = 36
    cam_data.clip_start = 0.005
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_blades = 7
    cam_data.dof.aperture_ratio = 1.0
    cam = C.link(bpy.data.objects.new("S01_Cam", cam_data), hero_col)
    scene.camera = cam
    aim = C.empty("CamAim", (0, 0, 0), hero_col)
    focus = C.empty("CamFocus", (0, 0, 0), hero_col)
    cam_data.dof.focus_object = focus
    tt = cam.constraints.new("TRACK_TO")
    tt.target = aim
    tt.track_axis, tt.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"

    dial = Vector((W.x, W.y, P.DIAL_Z + 0.001))
    path = [  # (frame, camera, aim, focus, f-stop)
        (1,           (-0.118, -0.050, 0.040), (-0.075, 0.050, 0.002), (-0.080, 0.035, 0.003), 5.6),
        (F["glide_mid"], (-0.040, -0.105, 0.052), (0.005, 0.000, 0.002), (0.000, 0.000, 0.003), 6.3),
        (F["turn"],   (0.075, -0.205, 0.075), (0.140, -0.080, 0.006), tuple(dial + Vector((-0.02, 0.015, 0))), 5.6),
        (F["hit"],    tuple(dial + Vector((-0.055, -0.178, 0.090))), tuple(dial + Vector((-0.002, -0.017, 0))), tuple(dial), 5.6),
        (F["end"],    tuple(dial + Vector((-0.030, -0.152, 0.112))), tuple(dial + Vector((-0.005, -0.021, 0))), tuple(dial), 6.3),
    ]
    for f, c, a_, fo, fs in path:
        C.key(cam, "location", f, c)
        C.key(aim, "location", f, a_)
        C.key(focus, "location", f, fo)
        C.key(cam_data.dof, "aperture_fstop", f, fs)
    for idb in (cam, aim, focus):
        C.set_interpolation(idb, "BEZIER", handle="AUTO_CLAMPED")

    # ---- clock mechanics: real time, 1 tick per second with a tiny recoil ------
    t0 = 16 * 3600 + 17 * 60 - B["hit"]   # clock time (s) at shot start
    for f in range(1, n_frames + 1):
        t = t0 + (f - 1) / C.FPS
        whole = math.floor(t)
        frac = t - whole
        # dead-beat second hand: snaps in ~3 frames, overshoots, settles
        if frac < 0.06:
            step = frac / 0.06 * 1.08
        elif frac < 0.14:
            step = 1.08 - (frac - 0.06) / 0.08 * 0.08
        else:
            step = 1.0
        sec_angle = ((whole - 1 + step) % 60) / 60 * math.tau
        minutes = (t / 60.0) % 60
        hours = (t / 3600.0) % 12
        C.key(watch["second"], "rotation_euler", f, -sec_angle, index=2)
        C.key(watch["minute"], "rotation_euler", f, -minutes / 60 * math.tau, index=2)
        C.key(watch["hour"], "rotation_euler", f, -hours / 12 * math.tau, index=2)
    for h in ("second", "minute", "hour"):
        C.set_interpolation(watch[h], "LINEAR")

    # ---- dust motes in the lamp light ---------------------------------------
    P.dust_field("Dust", (-0.22, -0.30, 0.004), (0.26, 0.12, 0.17), count=5200, radius=(0.00015, 0.0006),
                 collection=fx_col, mat=M.dust())

    # ---- titles (modern overlay; Mongolian Cyrillic, Noto, SIL OFL) ------------
    ts = TitleScene(scene, "S01_Titles")
    label = ts.text("ReconLabel", "Уран сайхны сэргээн дүрслэл", fonts["sans_regular"], 0.27,
                    (-7.25, -4.05, 0), color="#F1E4CC", strength=1.0, align_x="LEFT",
                    halo=0.0, plate=0.85)
    TitleScene.fade(label, C.sec(0.6 * s), C.sec(1.4 * s), peak=0.9)
    kicker = ts.text("Kicker", "МОНГОЛ ТӨРИЙН ТҮҮХЭН ЭРГЭЛТ", fonts["sans"], 0.30,
                     (0, -1.95, 0), color="#C8A56C", strength=1.1, spacing=1.25)
    big = ts.text("BigTime", "16:17", fonts["serif"], 1.35, (0, -2.75, 0), color="#F1E4CC", strength=1.25)
    date = ts.text("Date", "1924 оны 11 дүгээр сарын 26", fonts["serif_regular"], 0.42,
                   (0, -3.55, 0), color="#E8D6B7", strength=1.0)
    rule = ts.rule("Rule", 3.4, (0, -3.22, 0), color="#C8A56C", strength=1.1)
    ft, fe = F["title"], F["end"]
    TitleScene.fade(big, ft, ft + 0.7 * C.FPS * s)
    C.key(big, "location", ft, (0, -2.95, 0))
    C.key(big, "location", ft + 1.6 * C.FPS * s, (0, -2.75, 0))
    C.set_interpolation(big, "SINE", "EASE_OUT")
    TitleScene.fade(rule, ft + 0.3 * C.FPS * s, ft + 0.9 * C.FPS * s)
    C.key(rule, "scale", ft + 0.3 * C.FPS * s, (0.0, 1, 1))
    C.key(rule, "scale", ft + 1.3 * C.FPS * s, (3.4, 1, 1))
    C.set_interpolation(rule, "EXPO", "EASE_OUT")
    TitleScene.fade(date, ft + 0.6 * C.FPS * s, ft + 1.3 * C.FPS * s)
    TitleScene.fade(kicker, ft + 0.9 * C.FPS * s, ft + 1.7 * C.FPS * s, peak=0.95)

    build_compositor(scene, ts.scene, fade_in=(1, F["light_full"]))

    # ---- save / render -------------------------------------------------------
    if not args.no_save:
        C.save_blend(os.path.join(C.SCENES_DIR, "scene01.blend"))
    out = args.out or os.path.join(C.OUTPUT_DIR, f"scene01_{args.quality}_frames")
    if args.stills:
        C.render_frames(scene, out, stills=[int(x) for x in args.stills.split(",")])
    elif args.render:
        C.render_frames(scene, out, frames=C.frame_range_from_arg(args.frames, n_frames))


if __name__ == "__main__":
    main()
