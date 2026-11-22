"""END CREDITS (scene "09", 17 s)

0.0–8.8 s   student credits, large warm-gold serif on deep midnight blue:
            БҮТЭЭСЭН / БАТ-ОЧИР / ХҮСЛЭН / БАЯРБАЯСГАЛАН / 10Б АНГИ
8.8–17 s    secondary credits: narration, music, archival images actually used
            (with licence), research sources, software, fonts.
Background: a softly lit midnight-blue backdrop, slow camera drift and a few
gold dust motes (no flashy animation). Text is in the overlay scene, so it is
never blurred by depth of field.
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import archive as AR, common as C, materials as M, props as P  # noqa: E402
from lib.overlay import TitleScene  # noqa: E402
from lib.shot import Shot  # noqa: E402

NAMES = ["БАТ-ОЧИР", "ХҮСЛЭН", "БАЯРБАЯСГАЛАН"]
GOLD, GOLD_SOFT, IVORY = "#D9B46A", "#B89558", "#E8D6B7"


def secondary_text():
    used = [a for a in AR.manifest() if AR.asset(a)["path"]]
    arch = []
    for aid in used:
        e = AR.manifest()[aid]
        kind = "уран зураг" if "painting" in e["role"] else "гэрэл зураг"
        lic = "нийтийн өмч" if "public domain" in e["license_label"].lower() else e["license_label"]
        arch.append(f"{e['display_title']} ({kind})")
        arch.append(f"{AR.AUTHOR_MN.get(aid, e['author'])} · {lic} · Wikimedia Commons")
    lines = [
        "ХҮҮРНЭЛ  ·  ElevenLabs Eleven v4, «Bilguun» хоолой (elevenlabs.io)",
        "ХӨГЖИМ, ДУУ  ·  Төслийн эх бүтээл (кодоор синтезлэсэн)",
        "",
        "АРХИВЫН ДҮРС",
        *arch,
        "Бусад 3D дүрслэл нь уран сайхны сэргээн дүрслэл бөгөөд архивын бичлэг биш.",
        "",
        "ЭХ СУРВАЛЖ",
        "Монголын түүхийн тайлбар толь (ШУА) · Монгол Улсын Их Хурал (parliament.mn)",
        "БНМАУ-ын 1924 оны Үндсэн хууль (legalinfo.mn) · МОНЦАМЭ",
        "",
        "Blender · FFmpeg (нээлттэй эх)  ·  Фонт: Noto Serif / Noto Sans (SIL OFL)",
    ]
    return "\n".join(lines)


def main():
    sh = Shot("09", "Credits", 17.0, world_hex="#070b18", world_strength=1.0, samples_preview=12)
    t, END = sh.t, sh.n_frames
    sc = sh.scene
    # backdrop: large plane, gently lit, slightly lighter centre (midnight blue)
    back = P.box("Backdrop", (40, 0.1, 24), (0, 12, 0), None, M.flat("Midnight", "#0d1530", 0.9), bevel=0)
    glow = bpy.data.lights.new("BackGlow", "AREA")
    glow.size, glow.energy, glow.color = 10.0, 900.0, (0.55, 0.62, 0.9)
    go = C.link(bpy.data.objects.new("BackGlow", glow))
    go.location = (0, 2, 6)
    C.look_at(go, (0, 12, 0))
    dust_mat = M.emission("GoldMote", GOLD, 1.6)
    P.dust_field("Motes", (-9, 3, -5), (9, 10, 5), count=90, radius=(0.008, 0.02), wander=0.4,
                 drift=(0.0, 0.0, 0.05), mat=dust_mat)
    sc.cycles.samples = 2 if not sh.args.samples else sh.args.samples   # flat text on a plain backdrop
    cam, aim = sh.camera("Cam", 35, fstop=2.0)
    sh.move(cam, aim, [(1, (0.0, -10.0, 0.3), (0, 12, 0.0)), (END, (0.3, -8.8, 0.1), (0, 12, 0.0))])
    sh.cut("A", 1, cam)

    ts = sh.titles
    fps = sh.fps
    f_out0, f_out1 = t(8.0), t(8.8)
    head = ts.text("Head", "БҮТЭЭСЭН", sh.fonts["sans"], 0.34, (0, 2.3, 0), color=GOLD_SOFT,
                   strength=1.2, spacing=1.6, halo=0.0)
    TitleScene.fade(head, t(0.6), t(1.6), f_out0, f_out1)
    for i, n in enumerate(NAMES):
        o = ts.text(f"Name{i}", n, sh.fonts["serif"], 0.78, (0, 1.05 - i * 1.15, 0), color=GOLD,
                    strength=1.35, spacing=1.12, halo=0.0)
        TitleScene.fade(o, t(1.1 + 0.35 * i), t(2.3 + 0.35 * i), f_out0, f_out1)
    rule = ts.rule("Rule", 2.6, (0, -2.55, 0), color=GOLD_SOFT, thickness=0.02, strength=1.1)
    TitleScene.fade(rule, t(2.4), t(3.2), f_out0, f_out1)
    cls = ts.text("Class", "10Б АНГИ", sh.fonts["sans"], 0.42, (0, -3.2, 0), color=IVORY,
                  strength=1.2, spacing=1.5, halo=0.0)
    TitleScene.fade(cls, t(2.8), t(3.8), f_out0, f_out1)

    body = secondary_text()
    n_lines = body.count("\n") + 1
    size = 0.26 if n_lines <= 18 else 0.22
    top = min(4.1, n_lines * size * 1.3 / 2 + 0.2)
    sec = ts.text("Secondary", body, sh.fonts["sans_regular"], size, (0, top, 0), color=IVORY,
                  strength=1.05, halo=0.0)
    sec.data.align_y = "TOP"
    sec.data.space_line = 1.3
    TitleScene.fade(sec, t(9.2), t(10.2), t(16.0), END)
    sh.finish(fade_in=(1, t(1.0)))


if __name__ == "__main__":
    main()
