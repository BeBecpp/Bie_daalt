"""SCENE 08 — THE LEGACY  (storyboard 03:27–04:00, 33 s)

Shot A  sunrise over the steppe: long rising pull-back, the sun climbs.
Shot B  floating timeline of extruded year plates 1206 · 1911 · 1921 · 1924
        (crimson) → 1940 · 1960 · 1992 (constitutions renewed).
Shot C  back to the manuscript on the desk; film title; final ~5 s without
        narration: source card (bibliography) per 05_art_direction.md.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import common as C, materials as M, props as P, sets as S  # noqa: E402
from lib.overlay import TitleScene  # noqa: E402
from lib.shot import Shot  # noqa: E402

SOURCES = (
    "Эх сурвалж\n"
    "Монголын түүхийн тайлбар толь — ШУА Түүх, археологийн хүрээлэн (mongoltoli.mn)\n"
    "Монгол Улсын Их Хурал — old.parliament.mn/nn/63426, /nn/13466\n"
    "БНМАУ-ын анхдугаар Үндсэн хууль, 1924 — legalinfo.mn\n"
    "МОНЦАМЭ — Улс тунхагласны өдөр\n"
    "\n"
    "3D дүрслэлүүд нь уран сайхны сэргээн дүрслэл бөгөөд архивын бичлэг биш.\n"
    "Програм: Blender, FFmpeg (нээлттэй эх) · Фонт: Noto (SIL OFL)\n"
    "Дуу оруулалт: [нэр] · Найруулга, анимейшн: [сурагч / баг]"
)


def main():
    sh = Shot("08", "Legacy", 33.0, samples_preview=16)
    t, sc = sh.t, sh.scene
    A0, B0, C0, SRC, END = 1, t(12.5), t(23.0), t(28.0), sh.n_frames
    bg = S.sky_world(sc, sun_elev_deg=0.5, sun_rot_deg=100, strength=0.35)
    sky = next((n for n in sc.world.node_tree.nodes if n.bl_idname == "ShaderNodeTexSky"), None)
    if sky is not None:
        for f, e in ((1, math.radians(0.3)), (C0, math.radians(7.0))):
            sky.sun_elevation = e
            sky.keyframe_insert("sun_elevation", frame=f)
    steppe = S.steppe_set(grass_center=(0, 0), grass_size=60, grass_density=12, hills=12.0)
    gz = steppe["ground_z"]
    sun = bpy.data.lights.new("SunriseSun", "SUN")
    sun.color = C.kelvin_rgb(3000)
    sun.angle = math.radians(1.0)
    sun_obj = C.link(bpy.data.objects.new("SunriseSun", sun))
    for f, el, e in ((1, 0.5, 0.6), (C0, 7.0, 2.6)):
        C.key(sun_obj, "rotation_euler", f, (math.radians(-(90 - el)), 0, math.radians(12)))
        C.key(sun, "energy", f, e)

    # timeline plates
    brass = M.metal("Brass", "#C8A56C", 0.25)
    crimson = M.metal("CrimsonGold", "#9a3a2c", 0.3)
    steel = M.metal("Steel", "#a7a9ab", 0.3)
    years = (("1206", brass), ("1911", brass), ("1921", brass), ("1924", crimson),
             ("1940", steel), ("1960", steel), ("1992", steel))
    base_y, spacing = 55.0, 10.0
    plates = []
    for i, (yr, mat) in enumerate(years):
        x = -30 + i * spacing
        z = gz(x, base_y) + 6.0 + 0.6 * math.sin(i)
        txt = C.text_object(f"Year{yr}", yr, sh.fonts["serif"], size=2.4, extrude=0.18, location=(x, base_y, z))
        txt.data.bevel_depth = 0.025
        txt.rotation_euler.x = math.radians(90)
        txt.data.materials.append(mat)
        plates.append(txt)
        f_rise = B0 - int(0.5 * sh.fps) + int(i * 1.1 * sh.fps)
        C.key(txt, "location", 1, (x, base_y, z - 14.0))
        C.key(txt, "location", f_rise, (x, base_y, z - 14.0))
        C.key(txt, "location", f_rise + int(1.2 * sh.fps), (x, base_y, z))
        C.set_interpolation(txt, "BEZIER", handle="AUTO_CLAMPED")
    rail = P.box("TimelineRail", (spacing * 6 + 6, 0.06, 0.06),
                 (0, base_y + 0.2, gz(0, base_y) + 4.6), None, M.emission("RailGlow", "#C8A56C", 3.0), bevel=0)
    C.key(rail, "scale", B0 - 10, (0.0, 1, 1))
    C.key(rail, "scale", B0 + int(7.5 * sh.fps), (1.0, 1, 1))

    # desk + manuscript high above the terrain for the closing shot
    desk_o = Vector((0, 0, 400))
    desk = S.desk_set(args_quality(sh), sh.fonts, origin=tuple(desk_o))
    lamp, lamp_d = S.desk_key_light("DeskLamp", tuple(desk_o), None)
    for f, e in ((1, 0.0), (C0, 45.0)):
        C.key(lamp_d, "energy", f, e)
    C.set_interpolation(lamp_d, "CONSTANT")
    P.animate_watch(desk["watch"], C0 + int(2.0 * sh.fps), 1, END)

    camA, aimA = sh.camera("CamA_Sunrise", 32)
    sh.move(camA, aimA, [(A0, (-2, -12, gz(-2, -12) + 0.6), (0, 300, gz(0, 300) + 8)),
                         (B0, (6, -60, gz(6, -60) + 22), (20, 300, gz(20, 300) + 4))])
    camB, aimB = sh.camera("CamB_Timeline", 45)
    sh.move(camB, aimB, [(B0, (-42, base_y - 26, gz(-30, base_y) + 7.5), (-30, base_y, gz(-30, base_y) + 6)),
                         (C0, (34, base_y - 30, gz(30, base_y) + 8.5), (30, base_y, gz(30, base_y) + 6))])
    camC, aimC = sh.camera("CamC_Desk", 40, fstop=6.0)
    sh.move(camC, aimC, [(C0, desk_o + Vector((0.02, -0.42, 0.20)), desk_o + Vector((-0.02, -0.06, 0.0))),
                         (END, desk_o + Vector((0.06, -0.70, 0.38)), desk_o + Vector((0.0, -0.08, 0.0)))])
    sh.cut("A_sunrise", A0, camA)
    sh.cut("B_timeline", B0, camB)
    sh.cut("C_desk", C0, camC)

    ts = sh.titles
    sh.label(f_out=SRC)
    ts.band(t(1.0), SRC)
    sh.card("A_Line", "Монголын төрийн түүх нэг өдөр эхэлж, нэг өдөр дуусаагүй", 0.38, -3.55, t(1.5), B0 - 2,
            font="serif_regular")
    sh.card("B_Kicker", "ҮНДСЭН ХУУЛЬ ШИНЭЧЛЭГДСЭН ОНУУД: 1940 · 1960 · 1992", 0.28, -3.7,
            B0 + int(5.5 * sh.fps), C0 - 2, font="sans", color="#C8A56C", spacing=1.15)
    sh.card("C_Title", "16:17 — Монгол төрийн түүхэн эргэлт", 0.62, -2.9, C0 + int(0.6 * sh.fps), SRC,
            strength=1.25)
    sh.card("C_Day", "11 дүгээр сарын 26 · Улс тунхагласны өдөр", 0.34, -3.6, C0 + int(1.3 * sh.fps), SRC,
            font="sans", color="#C8A56C", spacing=1.08)
    # closing source card: black backdrop + bibliography (no narration here)
    black = ts.rule("SourceBackdrop", 20, (0, 0, -0.6), color="#000000", thickness=12, strength=0.0)
    TitleScene.fade(black, SRC - int(0.8 * sh.fps), SRC, peak=1.0)
    src = ts.text("Sources", SOURCES, sh.fonts["sans_regular"], 0.3, (0, 1.6, 0), color="#E8D6B7",
                  strength=1.0, halo=0.0)
    src.data.align_y = "TOP"
    src.data.space_line = 1.35
    TitleScene.fade(src, SRC + 4, SRC + int(0.8 * sh.fps), peak=1.0)
    sh.finish(fade_in=(1, t(1.5)))


def args_quality(sh):
    return sh.args.quality


if __name__ == "__main__":
    main()
