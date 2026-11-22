"""Typography overlay scene + compositor finishing (bloom, vignette,
subtle chromatic aberration, fade-in). Titles live in their own
orthographic scene so the main camera's depth of field never blurs them,
and they are clearly modern graphics (never painted onto the 'manuscript')."""
import bpy

from . import materials as M
from .common import set_interpolation, text_object


def _set(node, name, value):
    """Blender 4.2–4.5 moved many compositor node properties to sockets."""
    if name in node.inputs:
        node.inputs[name].default_value = value
        return True
    attr = name.lower().replace(" ", "_")
    if hasattr(node, attr):
        setattr(node, attr, value)
        return True
    print(f"[1617] note: {node.bl_idname} has no '{name}'")
    return False


class TitleScene:
    WIDTH = 16.0  # ortho units across the frame -> y spans +-4.5

    def __init__(self, main_scene, name="Titles"):
        self.main = main_scene
        sc = bpy.data.scenes.new(name)
        self.scene = sc
        sc.render.engine = main_scene.render.engine
        if sc.render.engine == "CYCLES":
            sc.cycles.samples = 4 if (main_scene.frame_step > 1 or main_scene.get("fast_final")) else 16
            sc.cycles.use_adaptive_sampling = True
            sc.cycles.max_bounces = 1
            sc.cycles.use_denoising = False
            sc.cycles.device = "CPU"
        sc.render.resolution_x = main_scene.render.resolution_x
        sc.render.resolution_y = main_scene.render.resolution_y
        sc.render.fps = main_scene.render.fps
        sc.frame_start, sc.frame_end = main_scene.frame_start, main_scene.frame_end
        sc.render.film_transparent = True
        sc.view_settings.view_transform = "Standard"
        cam_data = bpy.data.cameras.new(f"{name}_Cam")
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = self.WIDTH
        cam = bpy.data.objects.new(f"{name}_Cam", cam_data)
        cam.location = (0, 0, 10)
        sc.collection.objects.link(cam)
        sc.camera = cam
        world = bpy.data.worlds.new(f"{name}_World")
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
        sc.world = world

    def text(self, name, body, font, size, location, color="#E8D6B7", strength=1.0,
             align_x="CENTER", spacing=1.0, halo=0.4, plate=0.0):
        """Text with an optional soft dark halo (several offset copies) so it
        stays legible over bright parchment as well as the dark desk."""
        t = text_object(name, body, font, size=size, align_x=align_x, location=location,
                        collection=self.scene.collection, spacing=spacing)
        mat = M.overlay_text(f"{name}_Mat", color, strength)
        t.data.materials.append(mat)
        if halo:
            hmat = M.overlay_text(f"{name}_HaloMat", "#000000", 0.0)
            d = size * 0.06
            for i, (dx, dy) in enumerate(((d, -d), (-d, -d), (d, d), (-d, d), (0, -1.6 * d))):
                h = text_object(f"{name}_Halo{i}", body, font, size=size, align_x=align_x,
                                collection=self.scene.collection, spacing=spacing,
                                location=(dx, dy, -0.05))
                h.data.materials.append(hmat)
                h.parent = t
            t["halo_mat"] = hmat.name
            t["halo"] = halo
        if plate:
            # translucent dark plate sized to the evaluated text bounds
            dg = self.scene.view_layers[0].depsgraph
            dg.update()
            dims = t.evaluated_get(dg).dimensions
            w = dims.x if dims.x > 0 else len(body) * size * 0.52
            pad = size * 0.55
            pm = bpy.data.meshes.new(f"{name}_Plate")
            x0 = {"LEFT": 0.0, "CENTER": -w / 2, "RIGHT": -w}[align_x] - pad
            x1 = x0 + w + 2 * pad
            y0, y1 = -size * 0.62, size * 0.62
            pm.from_pydata([(x0, y0, -0.1), (x1, y0, -0.1), (x1, y1, -0.1), (x0, y1, -0.1)], [], [(0, 1, 2, 3)])
            po = bpy.data.objects.new(f"{name}_Plate", pm)
            self.scene.collection.objects.link(po)
            po.parent = t
            pm.materials.append(bpy.data.materials[t["halo_mat"]] if halo else
                                M.overlay_text(f"{name}_PlateMat", "#000000", 0.0))
            if not halo:
                t["halo_mat"] = pm.materials[0].name
            t["halo"] = plate
        return t

    def rule(self, name, width, location, color="#C8A56C", thickness=0.018, strength=1.0):
        bpy_mesh = bpy.data.meshes.new(name)
        w, h = 0.5, thickness / 2
        bpy_mesh.from_pydata([(-w, -h, 0), (w, -h, 0), (w, h, 0), (-w, h, 0)], [], [(0, 1, 2, 3)])
        obj = bpy.data.objects.new(name, bpy_mesh)
        obj.location = location
        obj.scale = (width, 1, 1)
        self.scene.collection.objects.link(obj)
        mat = M.overlay_text(f"{name}_Mat", color, strength)
        bpy_mesh.materials.append(mat)
        return obj

    def band(self, f_in, f_out, strength=1.0, fade=10):
        """Soft dark gradient across the lower third (stacked translucent
        strips) so captions read over bright parchment and dark desk alike."""
        n, top = 24, 3.4                      # strips over the bottom 3.4 units
        peaks = [0.62 * (1 - i / n) ** 1.6 for i in range(n)]
        strips = []
        h = top / n
        for i, pk in enumerate(peaks):
            y = -4.5 + h * i + h / 2
            st = self.rule(f"Band{i}_{int(f_in)}", self.WIDTH + 1, (0, y, -0.5), color="#000000",
                           thickness=h * 1.02, strength=0.0)
            TitleScene.fade(st, f_in, f_in + fade, f_out - fade, f_out, peak=pk * strength)
            strips.append(st)
        return strips

    @staticmethod
    def fade(obj, f_in, f_full, f_out=None, f_gone=None, peak=1.0):
        sock = obj.active_material.node_tree.nodes["Opacity"].inputs["Fac"]
        nt = obj.active_material.node_tree
        for f, v in ((f_in, 0.0), (f_full, peak)) + (((f_out, peak), (f_gone, 0.0)) if f_out else ()):
            sock.default_value = v
            sock.keyframe_insert("default_value", frame=f)
        set_interpolation(nt, "SINE", "EASE_IN_OUT")
        if "halo_mat" in obj:
            hnt = bpy.data.materials[obj["halo_mat"]].node_tree
            hs = hnt.nodes["Opacity"].inputs["Fac"]
            for f, v in ((f_in, 0.0), (f_full, peak)) + (((f_out, peak), (f_gone, 0.0)) if f_out else ()):
                hs.default_value = v * obj["halo"]
                hs.keyframe_insert("default_value", frame=f)
            set_interpolation(hnt, "SINE", "EASE_IN_OUT")


def build_compositor(main, titles_scene, fade_in=(1, 30), vignette=0.55, bloom=0.35):
    main.use_nodes = True
    nt = main.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links

    rl = N.new("CompositorNodeRLayers")
    rl.scene = main
    rl.location = (-900, 200)

    # filmic bloom on highlights (brass glints, light shaft)
    glare = N.new("CompositorNodeGlare")
    glare.location = (-650, 200)
    for gt in ("BLOOM", "FOG_GLOW"):
        try:
            glare.glare_type = gt
            break
        except TypeError:
            continue
    q = "LOW" if main.frame_step > 1 else "MEDIUM"
    _set(glare, "Quality", q) if "Quality" in glare.inputs else setattr(glare, "quality", q)
    _set(glare, "Threshold", 0.9)
    if not _set(glare, "Strength", bloom):
        _set(glare, "Mix", -1 + 2 * bloom)
    _set(glare, "Size", 0.6) if "Size" in glare.inputs else None
    L.new(rl.outputs["Image"], glare.inputs["Image"])

    # gentle lens dispersion
    lens = N.new("CompositorNodeLensdist")
    lens.location = (-420, 200)
    _set(lens, "Distortion", 0.0)
    _set(lens, "Dispersion", 0.012)
    L.new(glare.outputs["Image"], lens.inputs["Image"])

    # vignette: blurred ellipse mask multiplied in
    ell = N.new("CompositorNodeEllipseMask")
    ell.location = (-650, -200)
    if "Size" in ell.inputs:
        ell.inputs["Size"].default_value = (0.95, 0.85)
    else:
        ell.width, ell.height = 0.95, 0.85
    blur = N.new("CompositorNodeBlur")
    blur.location = (-420, -200)
    if "Size" in blur.inputs and blur.inputs["Size"].type == "VECTOR":
        blur.inputs["Size"].default_value = (250, 250)
    else:
        blur.use_relative = True
        blur.factor_x = blur.factor_y = 30
        blur.filter_type = "GAUSS"
    L.new(ell.outputs["Mask"], blur.inputs["Image"])
    vmix = N.new("CompositorNodeMixRGB")
    vmix.location = (-200, -200)
    vmix.blend_type = "MIX"
    vmix.inputs["Fac"].default_value = 1.0
    vmix.inputs[1].default_value = (1 - vignette, 1 - vignette, 1 - vignette, 1)
    L.new(blur.outputs["Image"], vmix.inputs[2])
    mul = N.new("CompositorNodeMixRGB")
    mul.location = (0, 150)
    mul.blend_type = "MULTIPLY"
    mul.inputs["Fac"].default_value = 1.0
    L.new(lens.outputs["Image"], mul.inputs[1])
    L.new(vmix.outputs["Image"], mul.inputs[2])

    # fade from black (scene-linear exposure, keyed)
    expo = N.new("CompositorNodeExposure")
    expo.name = "FadeExposure"
    expo.location = (200, 150)
    L.new(mul.outputs["Image"], expo.inputs["Image"])
    sock = expo.inputs["Exposure"]
    sock.default_value = -9.0
    sock.keyframe_insert("default_value", frame=fade_in[0])
    sock.default_value = 0.0
    sock.keyframe_insert("default_value", frame=fade_in[1])

    last = expo.outputs["Image"]
    if titles_scene is not None:
        rl2 = N.new("CompositorNodeRLayers")
        rl2.scene = titles_scene
        rl2.location = (200, -150)
        over = N.new("CompositorNodeAlphaOver")
        over.location = (450, 100)
        L.new(last, over.inputs[1])
        L.new(rl2.outputs["Image"], over.inputs[2])
        last = over.outputs["Image"]

    comp = N.new("CompositorNodeComposite")
    comp.location = (700, 100)
    L.new(last, comp.inputs["Image"])
    view = N.new("CompositorNodeViewer")
    view.location = (700, -100)
    L.new(last, view.inputs["Image"])
    main.render.use_compositing = True
    return nt


# --------------------------------------------------------------------------
# Animated counters (e.g. "77 төлөөлөгч"): text bodies updated per frame.
# --------------------------------------------------------------------------
COUNTER_HANDLER_SRC = '''
import bpy

def _ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def _1617_counters(scene, *args):
    f = scene.frame_current
    for ob in bpy.data.objects:
        if ob.type != "FONT" or "counter_fmt" not in ob:
            continue
        f0, f1 = ob["counter_f0"], ob["counter_f1"]
        v0, v1 = ob["counter_v0"], ob["counter_v1"]
        t = _ease((f - f0) / max(1, f1 - f0))
        body = ob["counter_fmt"].format(n=int(round(v0 + (v1 - v0) * t)))
        if ob.data.body != body:
            ob.data.body = body

def register():
    for h in list(bpy.app.handlers.frame_change_pre):
        if getattr(h, "__name__", "") == "_1617_counters":
            bpy.app.handlers.frame_change_pre.remove(h)
    bpy.app.handlers.frame_change_pre.append(_1617_counters)

register()
'''


def add_counter(obj, f0, f1, v0, v1, fmt="{n}"):
    obj["counter_f0"], obj["counter_f1"] = int(f0), int(f1)
    obj["counter_v0"], obj["counter_v1"] = int(v0), int(v1)
    obj["counter_fmt"] = fmt
    obj.data.body = fmt.format(n=v0)


def install_counter_handler():
    """Registers now and stores the handler as a text block that re-registers
    when the .blend is opened (needs 'Auto Run Python Scripts' in the GUI)."""
    txt = bpy.data.texts.get("1617_counters.py") or bpy.data.texts.new("1617_counters.py")
    txt.from_string(COUNTER_HANDLER_SRC)
    txt.use_module = True
    exec(compile(COUNTER_HANDLER_SRC, "1617_counters.py", "exec"), {"__name__": "1617_counters"})
    for sc in bpy.data.scenes:
        sc.render.use_lock_interface = True
