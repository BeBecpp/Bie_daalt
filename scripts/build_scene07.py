"""SCENE 07 — RIGHTS AND LIMITS  (storyboard 02:47–03:27, 40 s)

Minimal 3D motion graphics on a dark reflective floor:
A  a slab flips from ХААНТ ЗАСАГ to БҮГД НАЙРАМДАХ ЗАСАГ.
B  a row of anonymous figures lights up: Art. 34 — men and women aged 18+
   could vote and be elected UNDER SPECIFIC CRITERIA (not universal suffrage).
C  some figures go dark: Art. 35 — certain groups were excluded
   (e.g. former nobles, some lamas, usurers).
D  "not the same as today's democracy": achievements and limits together.
Sources: 03_fact_check_sources.md (legalinfo.mn 1924 text).
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import common as C, materials as M, props as P, sets as S  # noqa: E402
from lib.shot import Shot  # noqa: E402


def main():
    sh = Shot("07", "RightsLimits", 40.0, world_hex="#0c0b0a", world_strength=0.2)
    t, END = sh.t, sh.n_frames
    A0, B0, C0, D0 = 1, t(9.0), t(20.0), t(31.0)
    floor = P.box("Floor", (60, 60, 0.1), (0, 0, -0.05), None, M.flat("Floor", "#151311", 0.25, coat=0.6), bevel=0)

    # A: two-sided slab
    slab = C.empty("Slab", (0, -2.5, 1.4))
    body = P.box("SlabBody", (5.6, 0.25, 1.3), (0, 0, 0), None, M.flat("SlabMat", "#2a2420", 0.4, coat=0.4))
    body.parent = slab
    gold = M.metal("Brass", "#C8A56C", 0.3)
    crimson = M.flat("Crimson", "#9a3a32", 0.35, coat=0.5)
    front = C.text_object("Monarchy", "ХААНТ ЗАСАГ", sh.fonts["serif"], size=0.55, extrude=0.02,
                          location=(0, -0.14, 0))
    front.rotation_euler.x = math.radians(90)
    front.data.materials.append(gold)
    front.parent = slab
    back = C.text_object("Republic", "БҮГД НАЙРАМДАХ ЗАСАГ", sh.fonts["serif"], size=0.46, extrude=0.02,
                         location=(0, 0.14, 0))
    back.rotation_euler = (math.radians(90), 0, math.radians(180))
    back.data.materials.append(crimson)
    back.parent = slab
    C.key(slab, "rotation_euler", t(3.0), 0.0, index=2)
    C.key(slab, "rotation_euler", t(5.0), math.pi, index=2)
    C.key(slab, "location", B0 - 6, (0, -2.5, 1.4))
    C.key(slab, "location", B0 + int(1.2 * sh.fps), (0, 4, 9.0))   # rises out of frame for the next beat
    C.set_interpolation(slab, "BEZIER", handle="AUTO_CLAMPED")

    # B/C: row of anonymous standing figures
    me = S.figure_silhouette_mesh("person")
    mat = S.silhouette_material()
    me.materials.append(mat)
    figs = []
    n = 13
    excluded = {1, 4, 8, 11}            # symbolic subset: Art. 35 exclusions
    for i in range(n):
        f = C.link(bpy.data.objects.new(f"Citizen{i:02d}", me))
        f.location = (-6.0 + i * 1.0, 0.6, 0)
        f.rotation_euler.z = math.radians(180)
        f.color = (0, 0, 0, 1)
        figs.append(f)
        for fr, h in ((1, True), (B0, False)):
            C.key(f, "hide_render", fr, h)
        on = B0 + int((1.5 + 0.12 * i) * sh.fps)
        C.key(f, "color", on - 8, (0, 0, 0, 1))
        C.key(f, "color", on, (1, 1, 1, 1))
        if i in excluded:
            C.key(f, "color", C0 + int(1.2 * sh.fps), (1, 1, 1, 1))
            C.key(f, "color", C0 + int(2.0 * sh.fps), (0.0, 0.0, 0.0, 1))
        for fc in C.fcurves_of(f):
            if fc.data_path == "hide_render":
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
    spot = bpy.data.lights.new("RowLight", "SPOT")
    spot.spot_size, spot.spot_blend, spot.energy = math.radians(70), 0.5, 0.0
    spot.color = C.kelvin_rgb(4000)
    so = C.link(bpy.data.objects.new("RowLight", spot))
    so.location = (0, -5, 6)
    C.look_at(so, (0, 0.6, 0.8))
    for f, e in ((1, 0.0), (B0, 0.0), (B0 + int(1.5 * sh.fps), 2200.0), (END, 2200.0)):
        C.key(spot, "energy", f, e)
    key = bpy.data.lights.new("SlabKey", "AREA")
    key.size, key.energy = 4.0, 600.0
    ko = C.link(bpy.data.objects.new("SlabKey", key))
    ko.location = (-3, -5, 4)
    C.look_at(ko, (0, -2.5, 1.4))
    for f, e in ((1, 600.0), (B0, 600.0), (B0 + int(1.0 * sh.fps), 0.0)):
        C.key(key, "energy", f, e)

    cam, aim = sh.camera("Cam", 35, fstop=5.6)
    sh.move(cam, aim, [(A0, (0.6, -9.0, 1.6), (0, -2.5, 1.4)),
                       (B0, (0.0, -8.5, 1.9), (0, 0.6, 1.1)),
                       (C0, (-1.0, -8.0, 1.7), (0, 0.6, 1.0)),
                       (D0, (0.0, -10.5, 2.6), (0, 0.6, 1.1)),
                       (END, (0.6, -12.5, 3.2), (0, 0.6, 1.2))])
    sh.cut("A", 1, cam)

    sh.titles.band(t(1.0), END)
    sh.card("A1", "Хаант засгаас — бүгд найрамдах засагт", 0.5, -3.3, t(5.2), B0 - 2, font="serif_regular")
    sh.card("B1", "34-р зүйл", 0.32, -2.85, B0 + int(1.2 * sh.fps), C0 - 2, font="sans", color="#C8A56C",
            spacing=1.15)
    sh.card("B2", "18 нас хүрсэн эрэгтэй, эмэгтэй иргэд — тодорхой нөхцөлөөр", 0.42, -3.45,
            B0 + int(1.8 * sh.fps), C0 - 2, font="serif_regular")
    sh.card("B3", "сонгох, сонгогдох эрхтэй", 0.3, -4.0, B0 + int(2.4 * sh.fps), C0 - 2, font="sans_regular")
    sh.card("C1", "35-р зүйл", 0.32, -2.85, C0 + int(0.6 * sh.fps), D0 - 2, font="sans", color="#C8A56C",
            spacing=1.15)
    sh.card("C2", "Зарим нийгмийн бүлгийн эрхийг хязгаарласан", 0.44, -3.45, C0 + int(1.2 * sh.fps), D0 - 2,
            font="serif_regular")
    sh.card("C3", "жишээ нь: хуучин ноёд, зарим лам нар, мөнгө хүүлэгчид", 0.28, -4.0, C0 + int(2.0 * sh.fps),
            D0 - 2, font="sans_regular")
    sh.card("D1", "1924 оны тогтолцоо ≠ өнөөгийн ардчилал", 0.5, -3.2, D0 + int(0.5 * sh.fps), END + 30)
    sh.card("D2", "Ололт ба хязгаарлалтыг хамтад нь ойлгох", 0.32, -3.85, D0 + int(1.5 * sh.fps), END + 30,
            font="sans", color="#C8A56C", spacing=1.08)
    sh.finish(fade_in=(1, t(1.0)))


if __name__ == "__main__":
    main()
