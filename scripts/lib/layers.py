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
                        tone="#8a7356", image=None, caption=None, fit="height", recon="group"):
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
        # labelled artistic reconstruction: small silhouette diorama inside the frame
        _reconstruction(name, w, h, recon, collection, root)
        txt = C.text_object(f"{name}_Label", "Уран сайхны сэргээн дүрслэл\n(архивын зургийн оронд)",
                            fonts["sans"], size=h * 0.045, collection=collection,
                            location=(0, -0.03, -h * 0.40))
        txt.rotation_euler.x = 1.5708
        txt.data.align_y = "CENTER"
        txt.data.materials.append(M.emission(f"{name}_LabelMat", "#e8d6b7", 1.2))
        txt.parent = root
    if caption and not image:
        caption = None            # never show a photo credit on a reconstruction
    if image and caption:
        cap = C.text_object(f"{name}_Caption", caption, fonts["sans_regular"], size=max(0.13, h * 0.05), collection=collection,
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


def _reconstruction(name, w, h, kind, collection, root):
    """Dark silhouettes standing just in front of the print surface."""
    from mathutils import Matrix
    sil = bpy.data.materials.get("ReconSilhouette") or M.flat("ReconSilhouette", "#1a1612", 0.8)
    bm = bmesh.new()

    def cone(r1, r2, d, loc, seg=16):
        g = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=d)
        bmesh.ops.rotate(bm, verts=g["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(-1.5708, 3, "X"))
        bmesh.ops.translate(bm, verts=g["verts"], vec=loc)

    def blob(r, sc, loc):
        g = bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=9, radius=r)
        bmesh.ops.scale(bm, vec=sc, verts=g["verts"])
        bmesh.ops.translate(bm, verts=g["verts"], vec=loc)

    base = -h * 0.32
    if kind == "portrait":
        blob(h * 0.22, (1.0, 0.12, 0.9), (0, -0.02, base + h * 0.12))      # shoulders
        blob(h * 0.10, (1.0, 0.12, 1.15), (0, -0.03, base + h * 0.42))     # head
        cone(h * 0.12, h * 0.02, h * 0.03, (0, -0.03, base + h * 0.56))    # hat
    elif kind == "landscape":
        for i, x in enumerate((-0.32, -0.12, 0.06, 0.26)):
            r = h * (0.12 if i % 2 else 0.09)
            blob(r, (1.0, 0.1, 0.55), (x * w, -0.02, base + r * 0.3))       # ger / stupa bodies
            cone(r * 0.7, r * 0.05, 0.02, (x * w, -0.02, base + r * 0.9))
    else:  # group
        for i in range(7):
            x = (i - 3) * w * 0.12
            blob(h * 0.05, (1.0, 0.12, 1.0), (x, -0.02, base + h * 0.36))
            blob(h * 0.08, (0.75, 0.1, 1.5), (x, -0.02, base + h * 0.16))
    me = bpy.data.meshes.new(f"{name}_Recon")
    bm.to_mesh(me)
    bm.free()
    obj = C.link(bpy.data.objects.new(f"{name}_Recon", me), collection)
    me.materials.append(sil)
    obj.parent = root
    return obj
