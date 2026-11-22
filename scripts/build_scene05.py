"""SCENE 05 — 1924, A NEW SYSTEM  (storyboard 01:37–02:01, 24 s)

Shot A  oblique desk macro, daylight fading to lamp light: commission drafts
        are turned.  "1924 · 5 дугаар сар — Богд хаан таалал төгсөв"
Shot B  a small commission table seen from above: eight anonymous seated
        silhouettes around papers under a hanging lamp (no faces, no names).
        "Үндсэн хуулийн төсөл · хэд хэдэн үзэл баримтлал, гадаадын туршлага"
Shot C  back to the manuscript; "Бүгд найрамдах засаглал сонгогдов".
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import common as C, materials as M, props as P, sets as S  # noqa: E402
from lib.shot import Shot  # noqa: E402


def main():
    sh = Shot("05", "Decision1924", 27.0)
    t, END = sh.t, sh.n_frames
    A0, B0, C0 = 1, t(9.4), t(17.6)
    desk = S.desk_set(sh.args.quality, sh.fonts, origin=(0, 0, 0), with_watch=False)
    mats = [desk["paper_mat"], S.manuscript_material(sh.args.quality, seed=1925, name="ParchmentB")]
    drafts = P.page_stack("Draft", 8, (0.21, 0.30), mats, (0.02, -0.02, 0.0085),
                          collection=desk["collection"], rot_z=math.radians(-6))
    for i, pg in enumerate(drafts[:5]):
        f0 = t(2.0) + int(i * 1.1 * sh.fps)
        f1 = f0 + int(0.9 * sh.fps)
        C.key(pg, "rotation_euler", f0, 0.0, index=1)
        C.key(pg, "rotation_euler", f1, -math.pi, index=1)
        C.key(pg, "location", f0, pg.location.z, index=2)
        C.key(pg, "location", f1, 0.0085 + (i + 1) * 0.00045 + 0.0003, index=2)
        b = pg.modifiers["Curl"]
        for f, ang in ((f0, 0.0), ((f0 + f1) // 2, math.radians(-50)), (f1, 0.0)):
            b.angle = ang
            b.keyframe_insert("angle", frame=f)
    lamp, lamp_d = S.desk_key_light("DeskLamp", (0, 0, 0), None)
    win = bpy.data.lights.new("Daylight", "AREA")
    win.size, win.color = 1.5, (0.75, 0.85, 1.0)
    wo = C.link(bpy.data.objects.new("Daylight", win))
    wo.location = (1.2, 0.3, 0.9)
    C.look_at(wo, (0, 0, 0))
    for f, d, l in ((1, 40.0, 20.0), (B0, 6.0, 90.0), (END, 6.0, 90.0)):   # day fades, lamp takes over
        C.key(win, "energy", f, d)
        C.key(lamp_d, "energy", f, l)

    # commission table set (away from the desk)
    o = Vector((20, 0, 0))
    col = C.new_collection("Commission")
    P.box("CommTable", (2.2, 1.1, 0.06), tuple(o + Vector((0, 0, 0.75))), col, M.wood("CommWood"), bevel=0.01)
    P.box("CommFloor", (12, 12, 0.1), tuple(o + Vector((0, 0, -0.05))), col, M.flat("CommFloorMat", "#1c1612", 0.8),
          bevel=0)
    paper = M.flat("CommPaper", "#d9c7a3", 0.8)
    for k in range(6):
        P.box(f"CommPaper{k}", (0.21, 0.3, 0.003), tuple(o + Vector((-0.8 + k * 0.32, (k % 2) * 0.2 - 0.1, 0.782))),
              col, paper, rot_z=math.radians(-10 + 7 * k), bevel=0)
    me = S._figure_mesh()
    me.materials.append(S.silhouette_material())
    seats = [(-0.7, -0.85, 0), (0.0, -0.85, 0), (0.7, -0.85, 0), (-0.7, 0.85, 180), (0.0, 0.85, 180),
             (0.7, 0.85, 180), (-1.5, 0, -90), (1.5, 0, 90)]
    for i, (x, y, rz) in enumerate(seats):
        fig = C.link(bpy.data.objects.new(f"Member{i}", me), col)
        fig.location = o + Vector((x, y, 0.0))
        fig.rotation_euler.z = math.radians(rz)
        fig.color = (0.35, 0.35, 0.35, 1)
    hang = bpy.data.lights.new("HangingLamp", "POINT")
    hang.energy, hang.color, hang.shadow_soft_size = 0.0, C.kelvin_rgb(3000), 0.15
    ho = C.link(bpy.data.objects.new("HangingLamp", hang), col)
    ho.location = o + Vector((0, 0, 1.9))
    for f, e in ((1, 0.0), (B0, 220.0), (C0, 0.0)):
        C.key(hang, "energy", f, e)
    C.set_interpolation(hang, "CONSTANT")
    shade = P.cylinder("LampShade", 0.22, 0.12, tuple(o + Vector((0, 0, 1.98))), col, M.flat("Shade", "#2a1e14", 0.6))

    camA, aimA = sh.camera("CamA", 55, fstop=4.0)
    sh.move(camA, aimA, [(A0, (0.25, -0.30, 0.10), (0.06, 0.0, 0.01)), (B0, (0.16, -0.36, 0.20), (0.04, 0.0, 0.01))])
    camB, aimB = sh.camera("CamB", 30, fstop=5.6)
    sh.move(camB, aimB, [(B0, o + Vector((-2.6, -2.8, 3.4)), o + Vector((0, 0, 0.6))),
                         (C0, o + Vector((-0.6, -3.4, 3.0)), o + Vector((0, 0, 0.7)))])
    camC, aimC = sh.camera("CamC", 50, fstop=4.5)
    sh.move(camC, aimC, [(C0, (-0.12, -0.28, 0.12), (-0.04, 0.04, 0.0)), (END, (-0.02, -0.40, 0.22), (-0.03, 0.03, 0.0))])
    for pg in drafts:   # drafts gone for the final manuscript shot
        for f, h in ((1, False), (C0, True)):
            C.key(pg, "hide_render", f, h)
        C.set_interpolation(pg, "CONSTANT")
    sh.cut("A", A0, camA)
    sh.cut("B", B0, camB)
    sh.cut("C", C0, camC)

    P.dust_field("Dust", (-0.25, -0.45, 0.004), (0.3, 0.15, 0.25), count=2000, radius=(0.00015, 0.0006),
                 mat=M.dust())
    sh.label()
    sh.titles.band(t(1.0), END)
    sh.card("Date", "1924 · 5 дугаар сар", 0.55, -3.0, t(1.2), B0 - 2)
    sh.card("Bogd", "Богд хаан таалал төгсөв", 0.36, -3.75, t(2.0), B0 - 2, font="sans", color="#C8A56C",
            spacing=1.1)
    sh.card("Draft", "Үндсэн хуулийн төсөл", 0.55, -3.0, B0 + int(0.6 * sh.fps), C0 - 2)
    sh.card("Draft2", "Хэд хэдэн үзэл баримтлал, гадаад орны туршлагыг хэлэлцэв", 0.3, -3.75,
            B0 + int(1.2 * sh.fps), C0 - 2, font="sans_regular")
    sh.card("Choice", "Бүгд найрамдах засаглалын хэлбэр сонгогдов", 0.48, -3.3, C0 + int(0.8 * sh.fps), END + 30)
    sh.finish(fade_in=(1, t(1.0)))


if __name__ == "__main__":
    main()
