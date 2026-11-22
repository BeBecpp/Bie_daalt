"""SCENE 04 — 1921, CHANGE  (storyboard 01:10–01:37, 27 s)

Cool, desaturated 2.5D: archival PLACEHOLDER frames hanging at different
depths, tracked by a gently hand-held camera (low-amplitude noise, no random
jitter). Key fact on screen: the monarchy was NOT abolished in 1921; the
Bogd Khan remained head of state until his death in 1924.
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import common as C, layers as LY, materials as M, props as P  # noqa: E402
from lib.shot import Shot  # noqa: E402


def main():
    sh = Shot("04", "Change1921", 26.0, world_hex="#0f1214", world_strength=0.5)
    t, END = sh.t, sh.n_frames
    sh.scene.view_settings.look = "AgX - Base Contrast"
    LY.paper_backdrop("Backdrop", 26, 12, (0, 9, 0), tone="#8d949a")
    from lib import archive as AR
    for name, aid, size, loc, rz in (
            ("Revolutionaries1921", "s04_revolutionaries_1921", (3.6, 2.6), (1.2, 2.2, 0.45), -4),
            ("Kyakhta1921", "s04_kyakhta_1921", (3.0, 2.2), (6.6, 3.4, 0.2), 5)):
        a = AR.asset(aid)
        LY.archive_placeholder(name, size[0], size[1], sh.fonts, "АРХИВЫН ЗУРАГ\n(татагдаагүй — орлуулах газар)",
                               location=loc, rot=(0, 0, math.radians(rz)), tone="#7d8287", image=a["path"],
                               fit="width", caption=f"{a['caption']}\n{a['credit']}")
    # abstract document layers (labelled reconstruction) give depth around the photo
    from lib import sets as S
    docs = S.manuscript_material(sh.args.quality, seed=1921, name="DocSheet")
    for i, (loc, rz) in enumerate((((-3.6, 3.4, 0.2), 8), ((9.6, 5.4, -0.3), -7), ((-1.4, 5.6, 1.4), 3))):
        d = P.parchment_sheet(f"Doc{i}", size=(2.1, 2.97), res=(30, 42), mat=docs, seed=60 + i, curl=0.0)
        d.location = loc
        d.rotation_euler = (math.radians(90), 0, math.radians(rz))
    yr = C.text_object("Year1921", "1921", sh.fonts["serif"], size=1.6, extrude=0.08, location=(-1.6, -0.6, 1.25))
    yr.rotation_euler.x = math.radians(90)
    yr.data.bevel_depth = 0.012
    yr.data.materials.append(M.metal("Steel", "#b8bcc0", 0.3))
    P.dust_field("Dust", (-6, -3, -3), (10, 5, 3), count=1500, radius=(0.004, 0.01), wander=0.25,
                 drift=(0.04, 0.0, 0.02), mat=M.dust())
    key = bpy.data.lights.new("Key", "AREA")
    key.size, key.energy, key.color = 4.0, 1100, C.kelvin_rgb(6500)
    ko = C.link(bpy.data.objects.new("Key", key))
    ko.location = (-3, -4, 5)
    C.look_at(ko, (2, 2, 0))
    rim = bpy.data.lights.new("Rim", "AREA")
    rim.size, rim.energy, rim.color = 2.0, 250, C.kelvin_rgb(4200)
    ro = C.link(bpy.data.objects.new("Rim", rim))
    ro.location = (6, 6, 3)
    C.look_at(ro, (2, 2, 0))

    cam, aim = sh.camera("Cam", 35, fstop=3.2)
    sh.move(cam, aim, [(1, (-4.6, -5.2, 0.3), (-2.4, 2.0, -0.2)),
                       (t(13), (2.0, -5.6, 0.1), (2.2, 2.0, 0.0)),
                       (END, (7.0, -4.6, 0.5), (6.0, 3.0, 0.2))])
    # gentle hand-held feel: low-amplitude noise on the aim point (the camera
    # uses a Track-To constraint, so noise on its own rotation would be ignored)
    for fc in C.fcurves_of(aim):
        if fc.data_path == "location":
            mod = fc.modifiers.new("NOISE")
            mod.scale = 30.0
            mod.strength = 0.05
            mod.phase = fc.array_index * 17.0
    sh.cut("A", 1, cam)

    sh.label()
    sh.titles.band(t(1.0), END)
    sh.card("Rev", "1921 · Үндэсний ардчилсан хувьсгал", 0.5, -3.1, t(1.4), t(14.6))
    sh.card("Change", "Гадаадын цэргийн эзэрхийллээс ангижрах · шинэ төрийн байгуулал", 0.3, -3.8, t(8.3), t(14.6),
            font="sans_regular")
    sh.card("NotYet", "Гэхдээ хаант засаг тэр даруй халагдсангүй", 0.5, -3.1, t(15.0), END + 30)
    sh.card("Bogd", "Богд хаан 1924 он хүртэл төрийн тэргүүн хэвээр байв", 0.32, -3.8, t(18.1), END + 30,
            font="sans", color="#C8A56C")
    sh.finish(fade_in=(1, t(1.0)))


if __name__ == "__main__":
    main()
