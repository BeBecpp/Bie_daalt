"""SCENE 03 — 1911, INDEPENDENCE  (storyboard 00:48–01:10, 22 s)

2.5D layered parallax in smoky sepia: a paper backdrop, a framed archival
PLACEHOLDER (Bogd Khan photograph only once its rights are verified, see
ASSET_MANIFEST.md), drifting smoke/dust, an extruded date that rises and a
red ink line drawn beneath it (symbolic, not a border or route).
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import common as C, layers as LY, materials as M, props as P  # noqa: E402
from lib.shot import Shot  # noqa: E402


def extra(p):
    p.add_argument("--photo", default=None, help="rights-cleared Bogd Khan photograph (else placeholder)")


def main():
    sh = Shot("03", "Independence1911", 22.0, extra=extra, world_hex="#1a140e", world_strength=0.4)
    t, END = sh.t, sh.n_frames
    LY.paper_backdrop("Backdrop", 16, 9, (0, 6, 0), tone="#b59a72")
    LY.archive_placeholder("BogdKhanPhoto", 2.4, 3.1, sh.fonts,
                           "АРХИВЫН ЗУРАГ\n(эрх нь баталгаажаагүй —\nорлуулах газар)",
                           location=(-2.3, 2.0, 0.2), rot=(0, 0, math.radians(6)), image=sh.args.photo)
    LY.archive_placeholder("CityPhoto", 3.4, 2.2, sh.fonts, "АРХИВЫН ЗУРАГ\n(орлуулах газар)",
                           location=(3.4, 3.6, 0.9), rot=(0, 0, math.radians(-8)), tone="#7a6a55")
    # extruded date and its red underline drawn by the 'pen'
    brass = M.metal("Brass", "#C8A56C", 0.3)
    yr = C.text_object("Year1911", "1911", sh.fonts["serif"], size=1.5, extrude=0.08,
                       location=(1.6, 0.6, -0.6))
    yr.rotation_euler.x = math.radians(90)
    yr.data.bevel_depth = 0.012
    yr.data.materials.append(brass)
    C.key(yr, "location", 1, (1.6, 0.6, -1.4))
    C.key(yr, "location", t(4.0), (1.6, 0.6, -0.6))
    C.set_interpolation(yr, "BEZIER", handle="AUTO_CLAMPED")
    cu = bpy.data.curves.new("InkLine", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(2)
    for bp, co in zip(sp.bezier_points, ((-0.2, 0.55, -1.0), (1.6, 0.55, -1.08), (3.4, 0.55, -0.98))):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = 0.018
    line = C.link(bpy.data.objects.new("InkLine", cu))
    line.data.materials.append(M.flat("RedInk", "#782E2F", 0.4))
    cu.bevel_factor_end = 0.0
    cu.keyframe_insert("bevel_factor_end", frame=t(3.0))
    cu.bevel_factor_end = 1.0
    cu.keyframe_insert("bevel_factor_end", frame=t(6.5))
    # smoke-like haze and dust in front of the layers
    P.dust_field("Dust", (-6, -2.5, -3), (6, 4, 3), count=1800, radius=(0.004, 0.012), wander=0.25,
                 drift=(0.05, 0.0, 0.03), mat=M.dust())
    key = bpy.data.lights.new("Key", "AREA")
    key.size, key.energy, key.color = 3.0, 900, C.kelvin_rgb(3300)
    ko = C.link(bpy.data.objects.new("Key", key))
    ko.location = (-4, -3, 4)
    C.look_at(ko, (0, 2, 0))
    rim = bpy.data.lights.new("Rim", "AREA")
    rim.size, rim.energy, rim.color = 2.0, 300, C.kelvin_rgb(2600)
    ro = C.link(bpy.data.objects.new("Rim", rim))
    ro.location = (4, 5, 3)
    C.look_at(ro, (0, 2, 0))
    for f, e in ((1, 500), (t(8), 900), (END, 750)):
        C.key(key, "energy", f, e)

    cam, aim = sh.camera("Cam", 40, fstop=2.8)
    sh.move(cam, aim, [(1, (-3.5, -6.5, 0.6), (-1.5, 2.0, 0.2)),
                       (t(11), (0.5, -5.2, 0.0), (0.8, 1.5, -0.4)),
                       (END, (3.6, -6.0, 0.4), (2.4, 2.5, 0.2))])
    for f, fs in ((1, 2.8), (t(11), 4.0), (END, 3.2)):
        C.key(cam.data.dof, "aperture_fstop", f, fs)
    sh.cut("A", 1, cam)

    sh.label()
    sh.titles.band(t(1.0), END)
    sh.card("Date", "1911 оны 12 дугаар сарын 29", 0.55, -3.0, t(4.5), t(14))
    sh.card("State", "БОГД ХААНТ МОНГОЛ УЛС", 0.34, -3.75, t(5.5), t(14), font="sans", color="#C8A56C",
            spacing=1.25)
    sh.card("Line2", "Тусгаар тогтнолоо сэргээн тунхаглав", 0.46, -3.3, t(14.6), END + 30, font="serif_regular")
    sh.finish(fade_in=(1, t(1.0)))


if __name__ == "__main__":
    main()
