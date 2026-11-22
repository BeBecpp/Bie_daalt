"""SCENE 06 — 16:17, THE FIRST CONSTITUTION  (storyboard 02:01–02:47, 46 s)

Shot A  implied hall of the First Great Khural: 77 faceless seated
        silhouettes light up one by one, window light through haze.
        Counter "77 төлөөлөгч".                          (VO: sentences 1–2)
Shot B  the pocket watch reaches 16:17 on 26 November.     (VO: sentence 3)
Shot C  18-page manuscript montage, pages turning; "6 бүлэг · 50 зүйл".
                                                           (VO: sentence 4)
Shot D  a raking light sweeps the manuscript (Article 1 paraphrase), then
        the camera pulls back: "БҮГД НАЙРАМДАХ МОНГОЛ АРД УЛС · 1924".
                                                           (VO: sentences 5–6)

Guardrails: no opening date for the Khural; figures are anonymous
silhouettes (no invented faces); the manuscript is the abstract stand-in
unless --manuscript-image gives a rights-cleared scan; captions paraphrase
the narration and are not quotations.

    blender -b --factory-startup --python scripts/build_scene06.py -- --stills 150,460,640,900,1080
    blender -b --factory-startup --python scripts/build_scene06.py -- --duration 52 --render
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
from lib import sets as S            # noqa: E402
from lib.overlay import TitleScene, add_counter, build_compositor, install_counter_handler  # noqa: E402

DEFAULT_DURATION = 34.0     # fitted to the 29.07 s narration (lead 1.5 s)


def extra_args(p):
    p.add_argument("--manuscript-image", default=None)
    p.add_argument("--no-volume", action="store_true", help="skip hall haze (faster)")


def main():
    args = C.parse_args(extra_args)
    D = args.duration or DEFAULT_DURATION
    n_frames = int(round(D * C.FPS))
    scene = C.reset_scene("S06_Constitution")
    C.setup_render(scene, args, n_frames, samples_preview=24, samples_final=128)
    s = D / DEFAULT_DURATION
    t = lambda sec: C.sec(sec * s)          # beat (at 46 s) -> frame
    A0, B0, C0, D0 = 1, t(11.6), t(16.2), t(21.5)
    HIT = t(15.6)        # "...дөрвөн цаг арван долоон минут" ends at ~15.9 s
    TITLE = t(25.0)      # sentence 7: Бүгд Найрамдах Монгол Ард Улс
    END = n_frames

    world = bpy.data.worlds.new("S06_World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = C.hex_rgba("#11110F")
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3
    scene.world = world

    F = S.fonts()
    light_col = C.new_collection("Lights")
    cam_col = C.new_collection("Cameras")
    fx_col = C.new_collection("FX")

    # ------------------------------------------------------------ sets
    desk = S.desk_set(args.quality, F, origin=(0, 0, 0), manuscript_image=args.manuscript_image)
    hall = S.hall_set(origin=(30, 0, 0), volume=not (args.no_volume or args.rough))
    sky = bpy.data.objects["HallSkyCard"]
    sky.visible_shadow = False
    for o in hall["collection"].objects:      # the haze must not cast shadows either
        if o.name == "HallAir":
            o.visible_shadow = False

    # 18 manuscript pages (stand-in), on top of the main sheet, only in shot C
    page_mats = [desk["paper_mat"], S.manuscript_material(args.quality, seed=1925, name="ParchmentB"),
                 S.manuscript_material(args.quality, seed=1926, name="ParchmentC")]
    stack_c = Vector((-0.045, 0.02, 0.0085))
    pages = P.page_stack("Page", 18, (0.21, 0.30), page_mats,
                         (stack_c.x - 0.105, stack_c.y, stack_c.z), collection=desk["collection"],
                         rot_z=math.radians(3))
    for pg in pages:
        for f, hide in ((1, True), (C0, False), (D0, True)):
            C.key(pg, "hide_render", f, hide)
            C.key(pg, "hide_viewport", f, hide)
        C.set_interpolation(pg, "CONSTANT")
    turn_start = C0 + int(0.8 * C.FPS * s)
    turn_span = (D0 - turn_start) - int(0.8 * C.FPS * s)
    step = turn_span / len(pages)
    turn_len = max(8, int(0.6 * C.FPS * s))
    n = len(pages)
    for i, pg in enumerate(pages):
        f0 = int(turn_start + i * step)
        f1 = f0 + turn_len
        z_rest = pg.location.z
        z_left = stack_c.z + (i + 1) * 0.00045 + 0.0003
        C.key(pg, "rotation_euler", f0, 0.0, index=1)
        C.key(pg, "rotation_euler", f1, -math.pi, index=1)
        C.key(pg, "location", f0, z_rest, index=2)
        C.key(pg, "location", f1, z_left, index=2)
        bend = pg.modifiers["Curl"]
        for f, ang in ((f0, 0.0), ((f0 + f1) // 2, math.radians(-55)), (f1, 0.0)):
            bend.angle = ang
            bend.keyframe_insert("angle", frame=f)

    # ------------------------------------------------------------ figures light up
    figs = sorted(hall["figures"], key=lambda o: (-o.location.y, abs(o.location.x - 30)))
    lit0, lit1 = t(4.0), t(11.0)
    for i, fig in enumerate(figs):
        fo = int(lit0 + (lit1 - lit0) * i / (len(figs) - 1))
        C.key(fig, "color", max(1, fo - 8), (0.0, 0.0, 0.0, 1.0))
        C.key(fig, "color", fo, (1.0, 1.0, 1.0, 1.0))

    # ------------------------------------------------------------ lights
    sun_obj, sun = hall["sun"]
    fill_obj, fill = hall["fill"]
    for f, e in ((1, 9.0), (B0, 0.0)):
        C.key(sun, "energy", f, e)
    for f, e in ((1, 1500.0), (B0, 0.0)):
        C.key(fill, "energy", f, e)
    key_obj, key = S.desk_key_light("DeskLamp", (0, 0, 0), light_col)
    for f, e in ((1, 0.0), (B0, 100.0)):
        C.key(key, "energy", f, e)
    win = bpy.data.lights.new("DeskWindow", "AREA")
    win.size, win.color = 1.2, (0.7, 0.8, 1.0)
    win_obj = C.link(bpy.data.objects.new("DeskWindow", win), light_col)
    win_obj.location = (1.1, 0.4, 0.9)
    C.look_at(win_obj, (0, 0, 0))
    for f, e in ((1, 0.0), (B0, 9.0)):
        C.key(win, "energy", f, e)
    rim = bpy.data.lights.new("RimGlint", "AREA")
    rim.size, rim.color = 0.08, C.kelvin_rgb(3600)
    rim_obj = C.link(bpy.data.objects.new("RimGlint", rim), light_col)
    rim_obj.location = (0.30, 0.18, 0.10)
    C.look_at(rim_obj, tuple(desk["dial"]))
    for f, e in ((1, 0.0), (B0, 2.4), (C0, 0.0)):
        C.key(rim, "energy", f, e)
    for d in (sun, fill, key, win, rim):
        C.set_interpolation(d, "CONSTANT")
    # raking sweep light for Article 1 (shot D)
    sw = bpy.data.lights.new("Sweep", "SPOT")
    sw.spot_size, sw.spot_blend = math.radians(16), 0.8
    sw.color = C.kelvin_rgb(4300)
    sw.shadow_soft_size = 0.02
    sw_obj = C.link(bpy.data.objects.new("Sweep", sw), light_col)
    sw_tgt = C.empty("SweepTarget", (-0.2, 0.05, 0), light_col)
    tr = sw_obj.constraints.new("TRACK_TO")
    tr.target = sw_tgt
    tr.track_axis, tr.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    sw_obj.location = (-0.05, -0.55, 0.35)
    for f, x, e in ((1, -0.25, 0.0), (D0, -0.25, 0.0), (D0 + int(0.8 * C.FPS * s), -0.2, 70.0),
                    (TITLE, 0.18, 70.0), (TITLE + int(1.5 * C.FPS * s), 0.25, 0.0)):
        C.key(sw_tgt, "location", f, x, index=0)
        C.key(sw, "energy", f, e)

    # ------------------------------------------------------------ dust (desk)
    P.dust_field("Dust", (-0.22, -0.30, 0.004), (0.26, 0.12, 0.17), count=900,
                 radius=(0.00015, 0.0006), collection=fx_col, mat=M.dust())

    # ------------------------------------------------------------ cameras
    def camera(name, lens, fstop=None):
        cd = bpy.data.cameras.new(name)
        cd.lens, cd.sensor_width, cd.clip_start = lens, 36, 0.005
        cam = C.link(bpy.data.objects.new(name, cd), cam_col)
        aim = C.empty(f"{name}_Aim", (0, 0, 0), cam_col)
        tt = cam.constraints.new("TRACK_TO")
        tt.target = aim
        tt.track_axis, tt.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
        if fstop:
            cd.dof.use_dof = True
            cd.dof.aperture_fstop = fstop
            cd.dof.aperture_blades = 7
            cd.dof.focus_object = aim
        return cam, aim

    H = hall["origin"]
    camA, aimA = camera("CamA_Hall", 30, fstop=8.0)
    for f, c, a in ((A0, H + Vector((-0.3, -8.4, 1.15)), H + Vector((0, 5.6, 1.3))),
                    (B0, H + Vector((0.45, -0.9, 2.9)), H + Vector((0.1, 5.6, 0.9)))):
        C.key(camA, "location", f, tuple(c))
        C.key(aimA, "location", f, tuple(a))
    dial = desk["dial"]
    camB, aimB = camera("CamB_Watch", 70, fstop=5.0)
    for f, c in ((B0, dial + Vector((-0.045, -0.15, 0.115))), (C0, dial + Vector((0.004, -0.11, 0.105)))):
        C.key(camB, "location", f, tuple(c))
        C.key(aimB, "location", f, tuple(dial + Vector((0, -0.012, 0))))
    camC, aimC = camera("CamC_Pages", 45, fstop=5.6)
    for f, c, a in ((C0, stack_c + Vector((0.07, -0.33, 0.30)), stack_c + Vector((0.0, 0.01, 0))),
                    (D0, stack_c + Vector((-0.06, -0.25, 0.27)), stack_c + Vector((-0.02, 0.02, 0)))):
        C.key(camC, "location", f, tuple(c))
        C.key(aimC, "location", f, tuple(a))
    camD, aimD = camera("CamD_Article", 50, fstop=4.0)
    for f, c, a, fs in ((D0, (-0.13, -0.15, 0.085), (-0.05, 0.05, 0.004), 4.5),
                        (TITLE, (0.05, -0.50, 0.26), (0.0, 0.11, 0.004), 6.3),
                        (END, (0.10, -0.74, 0.40), (0.02, 0.13, 0.0), 8.0)):
        C.key(camD, "location", f, c)
        C.key(aimD, "location", f, a)
        C.key(camD.data.dof, "aperture_fstop", f, fs)
    for idb in (camA, aimA, camB, aimB, camC, aimC, camD, aimD):
        C.set_interpolation(idb, "BEZIER", handle="AUTO_CLAMPED")
    for name, f, cam in (("A_hall", A0, camA), ("B_watch", B0, camB), ("C_pages", C0, camC),
                         ("D_article", D0, camD)):
        m = scene.timeline_markers.new(name, frame=int(f))
        m.camera = cam
    scene.camera = camA

    P.animate_watch(desk["watch"], HIT, 1, END)

    # ------------------------------------------------------------ titles
    ts = TitleScene(scene, "S06_Titles")
    fps = C.FPS * s
    label = ts.text("ReconLabel", "Уран сайхны сэргээн дүрслэл", F["sans_regular"], 0.27,
                    (-7.25, -4.05, 0), color="#F1E4CC", strength=1.0, align_x="LEFT", halo=0.0, plate=0.85)
    TitleScene.fade(label, t(0.6), t(1.4), peak=0.9)
    ts.band(t(1.2), END)
    ts.band(D0, END + 30, strength=0.9)        # extra shade: captions over the bright manuscript

    def card(name, body, font, size, y, f_in, f_out, color="#F1E4CC", strength=1.1, spacing=1.0, x=0.0,
             align="CENTER", halo=0.45):
        o = ts.text(name, body, font, size, (x, y, 0), color=color, strength=strength, spacing=spacing,
                    align_x=align, halo=halo)
        TitleScene.fade(o, f_in, f_in + 0.6 * fps, f_out - 0.5 * fps, f_out)
        return o

    card("A_Kicker", "1924 · УЛСЫН АНХДУГААР ИХ ХУРАЛ", F["sans"], 0.32, -2.9, t(1.5), B0 - 2,
         color="#C8A56C", spacing=1.2)
    cnt = card("A_Count", "0 төлөөлөгч", F["serif"], 0.75, -3.65, t(2.0), B0 - 2)
    add_counter(cnt, lit0, lit1, 0, 77, "{n} төлөөлөгч")
    card("B_Date", "11 дүгээр сарын 26 · 16:17", F["serif"], 0.62, -3.55, HIT - int(0.3 * fps), C0 - 2)
    card("C_Head", "АНХДУГААР ҮНДСЭН ХУУЛЬ", F["sans"], 0.32, -2.75, C0 + int(0.4 * fps), D0 - 2,
         color="#C8A56C", spacing=1.2)
    card("C_Facts", "6 бүлэг · 50 зүйл", F["serif"], 0.72, -3.5, C0 + int(1.0 * fps), D0 - 2)
    pg = card("C_Pages", "0 / 18 хуудас", F["sans_regular"], 0.26, 4.0, turn_start, D0 - 2, x=7.25,
              align="RIGHT", halo=0.6)
    add_counter(pg, turn_start, turn_start + turn_span, 0, 18, "{n} / 18 хуудас")
    card("D_Article", "Эхний зүйл: улсын дээд эрх — жинхэнэ ардад", F["serif_regular"], 0.5, -3.55,
         D0 + int(0.9 * fps), TITLE - 2)
    # title sits in the dark upper third (over the background, not the bright page)
    big = ts.text("D_Title", "БҮГД НАЙРАМДАХ МОНГОЛ АРД УЛС", F["serif"], 0.78, (0, 3.35, 0),
                  color="#F1E4CC", strength=1.25, spacing=1.08, halo=0.5)
    TitleScene.fade(big, TITLE + int(0.3 * fps), TITLE + int(1.3 * fps))
    yr = ts.text("D_Year", "1924", F["serif_regular"], 0.56, (0, 2.45, 0), color="#D9B46A", strength=1.25,
                 halo=0.5)
    TitleScene.fade(yr, TITLE + int(0.9 * fps), TITLE + int(1.8 * fps))
    rule = ts.rule("D_Rule", 5.5, (0, 2.9, 0), color="#782E2F", thickness=0.03, strength=1.4)
    TitleScene.fade(rule, TITLE + int(0.6 * fps), TITLE + int(1.2 * fps))
    C.key(rule, "scale", TITLE + int(0.6 * fps), (0.0, 1, 1))
    C.key(rule, "scale", TITLE + int(1.8 * fps), (5.5, 1, 1))
    C.set_interpolation(rule, "EXPO", "EASE_OUT")

    install_counter_handler()
    build_compositor(scene, ts.scene, fade_in=(1, t(1.5)))

    if not args.no_save:
        C.save_blend(os.path.join(C.SCENES_DIR, "scene06.blend"))
    out = args.out or os.path.join(C.OUTPUT_DIR, f"scene06_{args.quality}_frames")
    if args.stills:
        C.render_frames(scene, out, stills=[int(x) for x in args.stills.split(",")])
    elif args.render:
        C.render_frames(scene, out, frames=C.frame_range_from_arg(args.frames, n_frames))


if __name__ == "__main__":
    main()
