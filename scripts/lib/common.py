"""Shared Blender helpers for the 16:17 documentary.

Everything here is plain bpy / mathutils and works in Blender 4.2–4.5 LTS.
Import from a scene builder that was launched with:

    blender -b --factory-startup --python scripts/build_sceneXX.py -- [options]
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONTS_DIR = os.path.join(PROJECT_ROOT, "assets", "fonts")
GEN_TEX_DIR = os.path.join(PROJECT_ROOT, "assets", "textures", "generated")
SCENES_DIR = os.path.join(PROJECT_ROOT, "scenes")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

FPS = 24

# Art-direction palette (05_art_direction.md), sRGB hex -> linear RGBA
PALETTE = {
    "charcoal": "#11110F",
    "parchment": "#E8D6B7",
    "copper": "#A46A3A",
    "gold": "#C8A56C",
    "crimson": "#782E2F",
}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def parse_args(extra=None):
    """Parse arguments that follow the `--` on the Blender command line."""
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--quality", choices=["preview", "final"], default="preview",
                   help="preview = 960x540 low samples, final = 1920x1080")
    p.add_argument("--engine", choices=["cycles", "eevee"], default="cycles",
                   help="eevee is fastest on a laptop GPU; cycles works everywhere (CPU)")
    p.add_argument("--duration", type=float, default=None,
                   help="shot length in seconds (stretch to the narration WAV)")
    p.add_argument("--render", action="store_true", help="render the animation after building")
    p.add_argument("--stills", default="", help="comma list of frames to render as stills, e.g. 1,96,192")
    p.add_argument("--frames", default="", help="frame range to render, e.g. 1-192")
    p.add_argument("--samples", type=int, default=None, help="override render samples")
    p.add_argument("--out", default=None, help="output folder for frames")
    p.add_argument("--no-save", action="store_true", help="do not write the .blend file")
    p.add_argument("--rough", action="store_true",
                   help="rough-cut profile: 4 samples, fast denoise, low bounces, every 2nd frame (12 fps)")
    if extra:
        extra(p)
    return p.parse_args(argv)


# --------------------------------------------------------------------------
# Colour helpers
# --------------------------------------------------------------------------
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(h, alpha=1.0):
    h = PALETTE.get(h, h).lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), alpha)


def kelvin_rgb(kelvin):
    """Approximate black-body colour (linear-ish) for light colours."""
    t = kelvin / 100.0
    if t <= 66:
        r = 255
        g = 99.4708025861 * math.log(t) - 161.1195681661
        b = 0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307
    else:
        r = 329.698727446 * ((t - 60) ** -0.1332047592)
        g = 288.1221695283 * ((t - 60) ** -0.0755148492)
        b = 255
    clamp = lambda v: max(0.0, min(255.0, v)) / 255.0
    return tuple(srgb_to_linear(clamp(v)) for v in (r, g, b))


# --------------------------------------------------------------------------
# Scene / render setup
# --------------------------------------------------------------------------
def reset_scene(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = name
    return scene


def _set_engine(scene, engine):
    if engine == "cycles":
        scene.render.engine = "CYCLES"
        return
    for ident in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = ident
            return
        except TypeError:
            continue


def setup_render(scene, args, frame_end, samples_preview=24, samples_final=96):
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = frame_end
    if args.quality == "preview":
        scene.render.resolution_x, scene.render.resolution_y = 960, 540
    else:
        scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"

    _set_engine(scene, args.engine)
    rough = getattr(args, "rough", False)
    samples = args.samples or (4 if rough else (samples_preview if args.quality == "preview" else samples_final))
    scene.frame_step = 2 if rough else 1
    if scene.render.engine == "CYCLES":
        c = scene.cycles
        c.device = "CPU"
        c.samples = samples
        c.use_adaptive_sampling = True
        c.adaptive_threshold = 0.03 if args.quality == "preview" else 0.01
        c.use_denoising = True
        try:
            c.denoiser = "OPENIMAGEDENOISE"
        except TypeError:
            pass
        c.max_bounces = 6
        c.diffuse_bounces = 2
        c.glossy_bounces = 3
        c.transmission_bounces = 6
        c.transparent_max_bounces = 8
        c.caustics_reflective = False
        c.caustics_refractive = False
        c.blur_glossy = 1.0
        scene.render.use_persistent_data = True
        if rough:
            c.adaptive_threshold = 0.08
            c.max_bounces, c.diffuse_bounces, c.glossy_bounces = 3, 1, 2
            c.transmission_bounces, c.transparent_max_bounces = 3, 6
            for attr, val in (("denoising_prefilter", "FAST"), ("denoising_quality", "FAST")):
                try:
                    setattr(c, attr, val)
                except (AttributeError, TypeError):
                    pass
    else:
        e = scene.eevee
        e.taa_render_samples = max(16, samples)
        for attr, val in (("use_raytracing", True), ("use_shadows", True),
                          ("shadow_ray_count", 2), ("shadow_step_count", 8),
                          ("use_gtao", True), ("use_soft_shadows", True)):
            if hasattr(e, attr):
                try:
                    setattr(e, attr, val)
                except Exception:
                    pass

    # Filmic highlight roll-off: AgX is Blender's open, ACES-like view transform.
    vs = scene.view_settings
    vs.view_transform = "AgX"
    try:
        vs.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    vs.exposure = 0.0
    vs.gamma = 1.0
    scene.render.film_transparent = False
    return scene


def frame_range_from_arg(s, default_end):
    if not s:
        return 1, default_end
    a, b = s.split("-")
    return int(a), int(b)


# --------------------------------------------------------------------------
# Timing helpers (beats are defined in seconds -> frames)
# --------------------------------------------------------------------------
def sec(t):
    """Seconds to (1-based) frame number."""
    return 1 + t * FPS


def key(obj, path, frame, value=None, index=-1, interp=None, handle=None):
    if value is not None:
        if index >= 0:
            getattr(obj, path)[index] = value
        else:
            setattr(obj, path, value)
    obj.keyframe_insert(data_path=path, frame=frame, index=index)
    ad = obj.animation_data if hasattr(obj, "animation_data") else None
    if ad and ad.action and (interp or handle):
        for fc in _action_fcurves(ad.action):
            if fc.data_path != path:
                continue
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 1e-4:
                    if interp:
                        kp.interpolation = interp
                    if handle:
                        kp.handle_left_type = kp.handle_right_type = handle


def _action_fcurves(action):
    """Blender 4.4+ layered actions keep fcurves in channelbags."""
    if hasattr(action, "fcurves") and len(action.fcurves):
        return list(action.fcurves)
    out = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                out.extend(bag.fcurves)
    return out


def fcurves_of(id_data):
    ad = getattr(id_data, "animation_data", None)
    if not ad or not ad.action:
        return []
    return _action_fcurves(ad.action)


def set_interpolation(id_data, interp="BEZIER", easing=None, handle=None):
    for fc in fcurves_of(id_data):
        for kp in fc.keyframe_points:
            kp.interpolation = interp
            if easing:
                kp.easing = easing
            if handle:
                kp.handle_left_type = kp.handle_right_type = handle


# --------------------------------------------------------------------------
# Objects
# --------------------------------------------------------------------------
def link(obj, collection=None):
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def new_collection(name, parent=None):
    col = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(col)
    return col


def empty(name, location=(0, 0, 0), collection=None, size=0.02):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_size = size
    obj.location = location
    return link(obj, collection)


def smooth(obj, angle_deg=40):
    me = obj.data
    for p in me.polygons:
        p.use_smooth = True
    try:
        obj.modifiers.new("AutoSmooth", "SMOOTH_BY_ANGLE")
        obj.modifiers["AutoSmooth"]["Input_1"] = math.radians(angle_deg)
    except Exception:
        pass


def load_font(filename):
    path = os.path.join(FONTS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Font missing: {path} (see assets/fonts/README.md)")
    return bpy.data.fonts.load(path, check_existing=True)


def text_object(name, body, font, size=1.0, align_x="CENTER", align_y="CENTER",
                extrude=0.0, collection=None, location=(0, 0, 0), spacing=1.0):
    cu = bpy.data.curves.new(name, type="FONT")
    cu.body = body
    cu.font = font
    cu.size = size
    cu.align_x = align_x
    cu.align_y = align_y
    cu.extrude = extrude
    cu.space_character = spacing
    obj = bpy.data.objects.new(name, cu)
    obj.location = location
    return link(obj, collection)


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def ensure_dirs(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)


def save_blend(path):
    ensure_dirs(os.path.dirname(path))
    # Textures stay external (relative paths) so they remain editable.
    bpy.ops.wm.save_as_mainfile(filepath=path, relative_remap=True)
    print(f"[1617] saved {path}")


def render_frames(scene, out_dir, frames=None, stills=None):
    ensure_dirs(out_dir)
    if stills:
        for f in stills:
            scene.frame_set(f)
            scene.render.filepath = os.path.join(out_dir, f"still_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
            print(f"[1617] still {f} -> {scene.render.filepath}")
        return
    if frames:
        scene.frame_start, scene.frame_end = frames
    scene.render.filepath = os.path.join(out_dir, "frame_")
    bpy.ops.render.render(animation=True)
