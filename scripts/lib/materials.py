"""Node-based materials that work in both EEVEE and Cycles."""
import bpy

from .common import hex_rgba


def _new(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    return mat, nt, out


def _bsdf(nt, **inputs):
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    for k, v in inputs.items():
        if k in b.inputs:
            b.inputs[k].default_value = v
    return b


def set_inputs(node, **vals):
    for k, v in vals.items():
        node.inputs[k].default_value = v


# --------------------------------------------------------------------------
def parchment(albedo_path, ink_path=None, name="Parchment"):
    mat, nt, out = _new(name)
    L = nt.links
    tc = nt.nodes.new("ShaderNodeTexCoord")
    img = nt.nodes.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(albedo_path, check_existing=True)
    img.interpolation = "Cubic"
    L.new(tc.outputs["UV"], img.inputs["Vector"])

    b = _bsdf(nt, Roughness=0.78)
    b.inputs["Subsurface Weight"].default_value = 0.08     # thin paper glows a bit
    b.inputs["Subsurface Radius"].default_value = (0.004, 0.003, 0.002)
    b.inputs["Subsurface Scale"].default_value = 0.002
    if "Sheen Weight" in b.inputs:
        b.inputs["Sheen Weight"].default_value = 0.25
    L.new(img.outputs["Color"], b.inputs["Base Color"])

    # paper tooth + fibres as bump
    noise = nt.nodes.new("ShaderNodeTexNoise")
    set_inputs(noise, Scale=900.0, Detail=6.0, Roughness=0.6)
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    set_inputs(noise2, Scale=60.0, Detail=3.0)
    mix = nt.nodes.new("ShaderNodeMath")
    mix.operation = "MULTIPLY_ADD"
    L.new(noise2.outputs["Fac"], mix.inputs[0])
    mix.inputs[1].default_value = 0.6
    L.new(noise.outputs["Fac"], mix.inputs[2])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.0004
    L.new(mix.outputs[0], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])

    if ink_path:
        ink = nt.nodes.new("ShaderNodeTexImage")
        ink.image = bpy.data.images.load(ink_path, check_existing=True)
        ink.image.colorspace_settings.name = "Non-Color"
        L.new(tc.outputs["UV"], ink.inputs["Vector"])
        # dried iron-gall / soot ink has a faint satin sheen
        rmap = nt.nodes.new("ShaderNodeMapRange")
        rmap.inputs["To Min"].default_value = 0.78
        rmap.inputs["To Max"].default_value = 0.42
        L.new(ink.outputs["Color"], rmap.inputs["Value"])
        L.new(rmap.outputs["Result"], b.inputs["Roughness"])
    L.new(b.outputs["BSDF"], out.inputs["Surface"])
    return mat


def wood(name="DeskWalnut"):
    mat, nt, out = _new(name)
    L = nt.links
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.6, 14.0, 1.0)    # long grain along X
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Y"
    set_inputs(wave, Scale=4.0, Distortion=4.5, **{"Detail": 6.0, "Detail Scale": 2.5, "Detail Roughness": 0.7})
    L.new(mp.outputs["Vector"], wave.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    set_inputs(noise, Scale=55.0, Detail=10.0)
    L.new(mp.outputs["Vector"], noise.inputs["Vector"])
    mixf = nt.nodes.new("ShaderNodeMix")
    mixf.data_type = "FLOAT"
    mixf.inputs["Factor"].default_value = 0.45
    L.new(wave.outputs["Fac"], mixf.inputs["A"])
    L.new(noise.outputs["Fac"], mixf.inputs["B"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = hex_rgba("#241409")
    ramp.color_ramp.elements[1].color = hex_rgba("#43281a")
    e = ramp.color_ramp.elements.new(0.55)
    e.color = hex_rgba("#2f1b0f")
    L.new(mixf.outputs["Result"], ramp.inputs["Fac"])
    b = _bsdf(nt, Roughness=0.32)
    b.inputs["Coat Weight"].default_value = 0.35             # old varnish
    b.inputs["Coat Roughness"].default_value = 0.18
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.25
    rr.inputs["To Max"].default_value = 0.55
    L.new(noise.outputs["Fac"], rr.inputs["Value"])
    L.new(rr.outputs["Result"], b.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.03
    L.new(mixf.outputs["Result"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    L.new(b.outputs["BSDF"], out.inputs["Surface"])
    return mat


def metal(name, color_hex, roughness=0.25, wear=True):
    mat, nt, out = _new(name)
    L = nt.links
    b = _bsdf(nt, Metallic=1.0, Roughness=roughness)
    b.inputs["Base Color"].default_value = hex_rgba(color_hex)
    if wear:
        noise = nt.nodes.new("ShaderNodeTexNoise")
        set_inputs(noise, Scale=420.0, Detail=10.0, Roughness=0.7)
        rr = nt.nodes.new("ShaderNodeMapRange")
        rr.inputs["To Min"].default_value = roughness * 0.6
        rr.inputs["To Max"].default_value = roughness * 1.8
        L.new(noise.outputs["Fac"], rr.inputs["Value"])
        L.new(rr.outputs["Result"], b.inputs["Roughness"])
        # micro scratches
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.05
        L.new(noise.outputs["Fac"], bump.inputs["Height"])
        L.new(bump.outputs["Normal"], b.inputs["Normal"])
    L.new(b.outputs["BSDF"], out.inputs["Surface"])
    return mat


def enamel(name="DialEnamel"):
    mat, nt, out = _new(name)
    L = nt.links
    b = _bsdf(nt, Roughness=0.12)
    b.inputs["Coat Weight"].default_value = 0.6
    noise = nt.nodes.new("ShaderNodeTexNoise")
    set_inputs(noise, Scale=80.0, Detail=4.0)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = hex_rgba("#efe6d2")
    ramp.color_ramp.elements[1].color = hex_rgba("#dccdae")    # age patina
    L.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    L.new(b.outputs["BSDF"], out.inputs["Surface"])
    return mat


def flat(name, color_hex, roughness=0.5, metallic=0.0, coat=0.0):
    mat, nt, out = _new(name)
    b = _bsdf(nt, Roughness=roughness, Metallic=metallic)
    b.inputs["Base Color"].default_value = hex_rgba(color_hex)
    b.inputs["Coat Weight"].default_value = coat
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    mat.diffuse_color = hex_rgba(color_hex)
    return mat


def glass(name="WatchCrystal", roughness=0.0, tint="#ffffff"):
    """Thin glass: fresnel-weighted gloss over a transparent BSDF.
    Unlike a refractive BSDF this lets shadow rays through in Cycles even
    with caustics disabled, so the dial under the crystal stays lit."""
    mat, nt, out = _new(name)
    L = nt.links
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = hex_rgba(tint)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = roughness
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.5
    # no reflection on back faces: avoids total internal reflection traps
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    L.new(geo.outputs["Backfacing"], inv.inputs[1])
    front = nt.nodes.new("ShaderNodeMath")
    front.operation = "MULTIPLY"
    L.new(fr.outputs["Fac"], front.inputs[0])
    L.new(inv.outputs[0], front.inputs[1])
    mx = nt.nodes.new("ShaderNodeMixShader")
    L.new(front.outputs[0], mx.inputs["Fac"])
    L.new(tr.outputs["BSDF"], mx.inputs[1])
    L.new(gl.outputs["BSDF"], mx.inputs[2])
    L.new(mx.outputs["Shader"], out.inputs["Surface"])
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND"),
                      ("use_transparent_shadow", True)):
        if hasattr(mat, attr):
            try:
                setattr(mat, attr, val)
            except Exception:
                pass
    return mat


def satin(name, color_hex):
    mat, nt, out = _new(name)
    b = _bsdf(nt, Roughness=0.35)
    b.inputs["Base Color"].default_value = hex_rgba(color_hex)
    b.inputs["Sheen Weight"].default_value = 1.0
    b.inputs["Sheen Tint"].default_value = hex_rgba("#e0a0a0")
    b.inputs["Specular IOR Level"].default_value = 0.6
    if "Anisotropic" in b.inputs:
        b.inputs["Anisotropic"].default_value = 0.6
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return mat


def emission(name, color_hex, strength=1.0):
    mat, nt, out = _new(name)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = hex_rgba(color_hex)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs["Emission"], out.inputs["Surface"])
    return mat


def dust(name="Dust"):
    """Tiny fibres/dust motes: bright only where the key light hits them."""
    mat, nt, out = _new(name)
    L = nt.links
    b = _bsdf(nt, Roughness=0.6)
    b.inputs["Base Color"].default_value = hex_rgba("#f2e6cf")
    b.inputs["Subsurface Weight"].default_value = 0.0
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tr.inputs["Color"].default_value = hex_rgba("#fff1d6")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.55
    L.new(b.outputs["BSDF"], mix.inputs[1])
    L.new(tr.outputs["BSDF"], mix.inputs[2])
    L.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def overlay_text(name, color_hex, strength=1.0):
    """Emission + animatable opacity (input 'Fac' of the mix, key it)."""
    mat, nt, out = _new(name)
    L = nt.links
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = hex_rgba(color_hex)
    e.inputs["Strength"].default_value = strength
    t = nt.nodes.new("ShaderNodeBsdfTransparent")
    m = nt.nodes.new("ShaderNodeMixShader")
    m.name = "Opacity"
    m.inputs["Fac"].default_value = 0.0
    L.new(t.outputs["BSDF"], m.inputs[1])
    L.new(e.outputs["Emission"], m.inputs[2])
    L.new(m.outputs["Shader"], out.inputs["Surface"])
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        if hasattr(mat, attr):
            try:
                setattr(mat, attr, val)
            except Exception:
                pass
    return mat
