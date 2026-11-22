"""2.5D layer helpers for the archive-style scenes (03, 04).

archive_placeholder() builds a framed, clearly labelled stand-in for an
archival photograph whose reuse rights are NOT verified. Swap in a real
image later with image=PATH (only after it is cleared in ASSET_MANIFEST.md).
"""
import bmesh
import bpy

from . import common as C
from . import materials as M


def _plane(name, w, h, collection=None, mat=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)], [],
                   [(0, 1, 2, 3)])
    me.uv_layers.new(name="UVMap")
    for i, uv in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        me.uv_layers[0].data[i].uv = uv
    obj = C.link(bpy.data.objects.new(name, me), collection)
    if mat:
        me.materials.append(mat)
    return obj


def photo_material(name, tone="#8a7356", image=None, grain=1.0):
    """Sepia/monochrome 'photo' surface. Procedural mottling only: it does not
    pretend to show a real person or place."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.55
    if image:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(image, check_existing=True)
        nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
        return mat
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 3.0
    n.inputs["Detail"].default_value = 10.0
    n.inputs["Roughness"].default_value = 0.65
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["UV"], n.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = C.hex_rgba("#2b241c")
    ramp.color_ramp.elements[1].color = C.hex_rgba(tone)
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
    # vignette burn toward the edges of the print
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (0.5, 0.5, 0)
    mp.inputs["Scale"].default_value = (1.6, 1.6, 1)
    sub = nt.nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (0.5, 0.5, 0)
    nt.links.new(tc.outputs["UV"], sub.inputs[0])
    nt.links.new(sub.outputs[0], grad.inputs["Vector"])
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 0.9
    nt.links.new(ramp.outputs["Color"], mul.inputs["A"])
    gr = nt.nodes.new("ShaderNodeValToRGB")
    gr.color_ramp.elements[0].color = (0.25, 0.25, 0.25, 1)
    gr.color_ramp.elements[1].color = (1, 1, 1, 1)
    gr.color_ramp.elements[1].position = 0.45
    nt.links.new(grad.outputs["Fac"], gr.inputs["Fac"])
    nt.links.new(gr.outputs["Color"], mul.inputs["B"])
    nt.links.new(mul.outputs["Result"], b.inputs["Base Color"])
    return mat


def _is_image(path):
    import os
    if not os.path.exists(path):
        return False
    with open(path, "rb") as fh:
        head = fh.read(8)
    return head.startswith(b"\xff\xd8\xff") or head.startswith(b"\x89PNG")


def archive_placeholder(name, w, h, fonts, label, location=(0, 0, 0), rot=(0, 0, 0), collection=None,
                        tone="#8a7356", image=None, caption=None, fit="height"):
    """Framed print on a card mount. With a rights-cleared image the print uses
    it (aspect taken from the file) and `caption` (attribution) sits under the
    mount; with no image a centred label marks it as a placeholder."""
    import os
    if image and not _is_image(image):
        print(f"[1617] {image} missing or not an image -> placeholder")
        image = None
    if image:
        img = bpy.data.images.load(image, check_existing=True)
        ar = img.size[0] / max(1, img.size[1])
        if fit == "height":
            w = h * ar
        else:
            h = w / ar
    root = C.empty(name, location, collection, size=0.2)
    root.rotation_euler = rot
    mount = _plane(f"{name}_Mount", w * 1.12, h * 1.14, collection, M.flat(f"{name}_MountMat", "#d9ccb0", 0.9))
    mount.parent = root
    mount.location.y = 0.004
    photo = _plane(f"{name}_Photo", w, h, collection, photo_material(f"{name}_PhotoMat", tone, image))
    photo.parent = root
    if not image:
        txt = C.text_object(f"{name}_Label", label, fonts["sans"], size=h * 0.055, collection=collection,
                            location=(0, -0.004, 0))
        txt.rotation_euler.x = 1.5708
        txt.data.align_y = "CENTER"
        txt.data.materials.append(M.emission(f"{name}_LabelMat", "#e8d6b7", 1.2))
        txt.parent = root
    if image and caption:
        cap = C.text_object(f"{name}_Caption", caption, fonts["sans_regular"], size=0.11, collection=collection,
                            location=(0, -0.01, -h * 0.57 - 0.16))
        cap.rotation_euler.x = 1.5708
        cap.data.materials.append(M.emission(f"{name}_CaptionMat", "#e8d6b7", 1.0))
        cap.parent = root
    return root


def paper_backdrop(name, w, h, location, collection=None, tone="#cdb894"):
    mat = photo_material(f"{name}_Mat", tone)
    p = _plane(name, w, h, collection, mat)
    p.location = location
    return p
