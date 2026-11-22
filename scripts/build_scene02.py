"""SCENE 02 — 1206, THE FOUNDATION  (storyboard 00:17–00:48, 31 s)

Shot A  golden dawn, low in wind-blown grass; a line of riders crosses the
        ridge in silhouette against the sun.  "1206 · ИХ МОНГОЛ УЛС"
Shot B  overhead orbit of a ring of gers around a central ger: a symbol of
        the khuraldai (assembly), not a reconstruction of a specific event.
        "ИХ ХУРАЛДАЙ" + caveat that it is not a modern parliament.
Shot C  low pass toward the central ger at the khan's tent door; caption
        "«Их засаг»: бүрэн эх нь уламжлагдаагүй".

Guardrails: no face/actor for Chinggis Khan; no invented Yassa text;
no borders; the Khuraldai is not presented as a modern legislature.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import common as C, materials as M, props as P, sets as S  # noqa: E402
from lib.shot import Shot  # noqa: E402


def main():
    sh = Shot("02", "Foundation1206", 31.0, samples_preview=16)
    t, sc = sh.t, sh.scene
    A0, B0, C0, END = 1, t(12.0), t(22.0), sh.n_frames
    S.sky_world(sc, sun_elev_deg=3.5, sun_rot_deg=100, strength=0.35)
    steppe = S.steppe_set(grass_center=(0, 0), grass_size=60, grass_density=14, hills=12.0)
    gz = steppe["ground_z"]

    sun = bpy.data.lights.new("DawnSun", "SUN")
    sun.color = C.kelvin_rgb(2900)
    sun.energy = 2.4
    sun.angle = math.radians(1.0)
    sun_obj = C.link(bpy.data.objects.new("DawnSun", sun))
    sun_obj.rotation_euler = (math.radians(-86.5), 0, math.radians(12))   # backlight from +Y

    sil_mat = M.flat("Silhouette", "#14110e", 0.8)
    rider_me = S.figure_silhouette_mesh("rider")
    rider_me.materials.append(sil_mat)
    riders = []
    for i in range(7):
        r = bpy.data.objects.new(f"Rider{i}", rider_me)
        C.link(r)
        riders.append(r)
    # riders move along a ridge line ~140 m away, left -> right
    ridge_y = 140.0
    for i, r in enumerate(riders):
        x0, x1 = -62 - i * 7, 40 - i * 7
        for f, x in ((1, x0), (B0, x1)):
            C.key(r, "location", f, (x, ridge_y + (i % 2) * 4, gz(x, ridge_y) + 0.1))
        r.rotation_euler.z = math.radians(-90)
        r.scale = (1.6, 1.6, 1.6)
        for f in range(1, B0, 4):  # gallop bob
            C.key(r, "rotation_euler", f, math.radians(3.0 * math.sin(f * 0.9 + i)), index=0)
        C.set_interpolation(r, "LINEAR")

    # ring of gers (khuraldai symbol) on a flat area to the north-east
    gc = Vector((420.0, 300.0, 0.0))
    gc.z = gz(gc.x, gc.y)
    felt = M.flat("Felt", "#d8cdb6", 0.95)
    felt_dark = M.flat("FeltDark", "#b9ab90", 0.95)
    S.ger("GerCentral", tuple(gc), None, radius=5.5, mat=felt)
    rng = random.Random(1206)
    for k in range(18):
        a = k / 18 * math.tau
        p = gc + Vector((math.cos(a) * 38, math.sin(a) * 38, 0))
        p.z = gz(p.x, p.y)
        S.ger(f"Ger{k}", tuple(p), None, radius=rng.uniform(2.6, 3.4), mat=felt if k % 3 else felt_dark)
    people_me = S.figure_silhouette_mesh("person")
    people_me.materials.append(sil_mat)
    for k in range(40):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(12, 26)
        p = gc + Vector((math.cos(a) * d, math.sin(a) * d, 0))
        p.z = gz(p.x, p.y)
        o = bpy.data.objects.new(f"Person{k}", people_me)
        o.location = p
        o.rotation_euler.z = a + math.pi / 2
        C.link(o)

    camA, aimA = sh.camera("CamA_Grass", 85, fstop=4.0)
    sh.move(camA, aimA, [(A0, (-6, -14, gz(-6, -14) + 0.7), (-40, ridge_y, gz(-40, ridge_y) + 3)),
                         (B0, (5, -9, gz(5, -9) + 1.3), (0, ridge_y, gz(0, ridge_y) + 3))])
    camA.data.dof.focus_distance = 140
    camA.data.dof.focus_object = None
    camB, aimB = sh.camera("CamB_Overhead", 28)
    keysB = []
    for i, f in enumerate((B0, (B0 + C0) // 2, C0)):
        a = math.radians(200 + 35 * i)
        keysB.append((f, gc + Vector((math.cos(a) * 75, math.sin(a) * 75, 95 - 10 * i)), gc))
    sh.move(camB, aimB, keysB)
    camC, aimC = sh.camera("CamC_Approach", 40, fstop=4.0)
    ap = math.radians(250)            # between two ring gers (every 20 degrees, at 240 and 260)
    pc0 = gc + Vector((math.cos(ap) * 62, math.sin(ap) * 62, 0))
    pc1 = gc + Vector((math.cos(ap) * 20, math.sin(ap) * 20, 0))
    pc0.z, pc1.z = gz(pc0.x, pc0.y) + 2.2, gz(pc1.x, pc1.y) + 1.9
    sh.move(camC, aimC, [(C0, pc0, gc + Vector((0, 0, 2.5))), (END, pc1, gc + Vector((0, 0, 2.2)))])
    sh.cut("A_dawn", A0, camA)
    sh.cut("B_overhead", B0, camB)
    sh.cut("C_approach", C0, camC)

    ts = sh.titles
    sh.label()
    ts.band(t(1.0), END)
    sh.card("Year", "1206", 1.25, -2.85, t(2.0), B0 - 2)
    sh.card("State", "ИХ МОНГОЛ УЛС", 0.36, -3.75, t(3.0), B0 - 2, font="sans", color="#C8A56C", spacing=1.25)
    sh.card("Khuraldai", "ИХ ХУРАЛДАЙ", 0.36, -2.95, B0 + int(0.6 * sh.fps), C0 - 2, font="sans",
            color="#C8A56C", spacing=1.25)
    sh.card("KhuraldaiNote", "Төрийн чухал асуудлыг хэлэлцдэг байсан ч дээд эрх хаанд төвлөрч байв",
            0.30, -3.65, B0 + int(1.4 * sh.fps), C0 - 2, font="sans_regular")
    sh.card("Yassa", "«Их засаг» — бүрэн эх нь өнөөдөр уламжлагдаагүй", 0.40, -3.5,
            C0 + int(1.2 * sh.fps), END + 40, font="serif_regular")
    sh.finish(fade_in=(1, t(1.2)))


if __name__ == "__main__":
    main()
