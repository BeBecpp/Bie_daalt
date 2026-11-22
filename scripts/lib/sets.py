"""Reusable sets shared by several scenes.

desk_set()  - the 1924 desk: manuscript sheet(s), pocket watch + chain,
              red silk ribbon, books, inkwell (Scene 01 look; Scenes 05/06).
hall_set()  - an *implied* 1924 assembly hall built from silhouettes:
              benches, faceless seated figures, tall windows, presidium
              table. Deliberately abstract: we do not know (and do not
              claim) the real interior or the delegates' appearance.
"""
import math

import bpy
from mathutils import Vector

from . import common as C
from . import materials as M
from . import props as P
from . import textures as T


def fonts():
    return {"serif": C.load_font("NotoSerif-SemiBold.ttf"),
            "serif_regular": C.load_font("NotoSerif-Regular.ttf"),
            "sans": C.load_font("NotoSans-Medium.ttf"),
            "sans_regular": C.load_font("NotoSans-Regular.ttf")}


def manuscript_material(quality, seed=1924, image=None, name="Parchment"):
    if image:
        return M.parchment(image, None, name=name)
    w = 2048 if quality == "preview" else 4096
    albedo, ink = T.make_manuscript_textures(C.GEN_TEX_DIR, width=w, seed=seed)
    return M.parchment(albedo, ink, name=name)


def desk_set(quality, font_set, origin=(0, 0, 0), manuscript_image=None, with_watch=True,
             collection=None):
    o = Vector(origin)
    col = collection or C.new_collection("DeskSet")
    out = {"collection": col, "origin": o}
    out["desk"] = P.box("Desk", (2.4, 1.6, 0.04), tuple(o + Vector((0, 0.3, -0.02))), col, M.wood(), bevel=0)
    P.box("Wall", (4.0, 0.05, 2.0), tuple(o + Vector((0, 1.5, 0.9))), col,
          M.flat("Plaster", "#2a2520", roughness=0.9), bevel=0)

    paper_mat = manuscript_material(quality, image=manuscript_image)
    paper = P.parchment_sheet("Manuscript", mat=paper_mat, collection=col)
    paper.location = o + Vector((-0.04, 0.03, 0.0))
    paper.rotation_euler.z = math.radians(4)
    out["paper"] = paper
    out["paper_mat"] = paper_mat

    P.ribbon("RedRibbon", [tuple(o + Vector(p)) for p in
                           ((-0.10, 0.12, 0.0016), (-0.16, 0.02, 0.0004), (-0.20, -0.10, 0.0004),
                            (-0.17, -0.21, 0.0006), (-0.09, -0.29, 0.0004), (0.02, -0.33, 0.0004))],
             width=0.014, collection=col, mat=M.satin("CrimsonSilk", "#782E2F"), twist=0.25)

    if with_watch:
        W = o + Vector((0.17, -0.10, 0.0))
        watch = P.pocket_watch("Watch", font_set, collection=col)
        watch["root"].location = W
        watch["root"].rotation_euler.z = math.radians(-8)
        a = math.radians(-8)

        def wp(x, y, z=0.0006):
            return (W.x + x * math.cos(a) - y * math.sin(a), W.y + x * math.sin(a) + y * math.cos(a), z + o.z)

        P.chain("WatchChain", [wp(0, 0.044), wp(0.012, 0.07), wp(0.05, 0.085), wp(0.085, 0.06),
                               wp(0.12, 0.05), wp(0.17, 0.08), wp(0.26, 0.12)],
                collection=col, mat=bpy.data.materials["Brass"])
        out["watch"] = watch
        out["dial"] = Vector((W.x, W.y, o.z + P.DIAL_Z + 0.001))

    leather = [M.flat("LeatherOx", "#3b1612", 0.55, coat=0.2), M.flat("LeatherBrown", "#3a2615", 0.6, coat=0.2),
               M.flat("LeatherDark", "#1f1a14", 0.5, coat=0.2)]
    for i, (sz, rz) in enumerate((((0.24, 0.17, 0.035), 0.06), ((0.22, 0.16, 0.03), -0.05),
                                  ((0.20, 0.15, 0.028), 0.14))):
        P.box(f"Book{i}", sz, tuple(o + Vector((0.02 + 0.01 * i, 0.50, 0.0175 + i * 0.033))), col,
              leather[i], rot_z=rz)
    P.cylinder("Inkwell", 0.026, 0.05, tuple(o + Vector((-0.27, 0.27, 0.025))), col, M.glass("InkwellGlass", 0.05))
    P.cylinder("InkwellInk", 0.022, 0.03, tuple(o + Vector((-0.27, 0.27, 0.016))), col, M.flat("Ink", "#050404", 0.05))
    brass = bpy.data.materials.get("Brass") or M.metal("Brass", "#C8A56C", 0.22)
    P.cylinder("InkwellLid", 0.017, 0.012, tuple(o + Vector((-0.27, 0.27, 0.056))), col, brass)
    for i, (x, y, z) in enumerate(((0.75, 1.3, 0.42), (0.95, 1.35, 0.30), (-0.85, 1.4, 0.5))):
        P.cylinder(f"Practical{i}", 0.012, 0.02, tuple(o + Vector((x, y, z))), col,
                   M.emission(f"PracticalGlow{i}", "#ffb36b", 40.0), segments=16)
    return out


def desk_key_light(name, origin, collection, kelvin=3700):
    """Spot 'desk lamp' aimed at the manuscript; returns (light_obj, light_data)."""
    o = Vector(origin)
    tgt = C.empty(f"{name}Target", tuple(o + Vector((0.05, -0.04, 0.0))), collection)
    d = bpy.data.lights.new(name, "SPOT")
    d.color = C.kelvin_rgb(kelvin)
    d.spot_size = math.radians(55)
    d.spot_blend = 0.65
    d.shadow_soft_size = 0.035
    obj = C.link(bpy.data.objects.new(name, d), collection)
    obj.location = o + Vector((-0.6, 0.32, 0.43))
    tr = obj.constraints.new("TRACK_TO")
    tr.target = tgt
    tr.track_axis, tr.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    return obj, d


# --------------------------------------------------------------------------
def _figure_mesh():
    """One faceless seated silhouette (shared mesh data)."""
    import bmesh
    bm = bmesh.new()
    # torso: tapered 8-sided prism
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.21, radius2=0.17, depth=0.62)
    bmesh.ops.scale(bm, vec=(1.0, 0.62, 1.0), verts=bm.verts)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.78))
    head = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.105)
    bmesh.ops.scale(bm, vec=(1.0, 1.0, 1.12), verts=head["verts"])
    bmesh.ops.translate(bm, verts=head["verts"], vec=(0, 0.01, 1.22))
    neck = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.055, radius2=0.05, depth=0.12)
    bmesh.ops.translate(bm, verts=neck["verts"], vec=(0, 0, 1.11))
    # thighs (seated) pointing forward (+Y)
    legs = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(0.36, 0.42, 0.14), verts=legs["verts"])
    bmesh.ops.translate(bm, verts=legs["verts"], vec=(0, 0.17, 0.52))
    me = bpy.data.meshes.new("FigureSilhouette")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me


def silhouette_material():
    """Dark figures; Object Info colour lets each one be 'lit' individually."""
    mat, nt = bpy.data.materials.new("Silhouette"), None
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.7
    info = nt.nodes.new("ShaderNodeObjectInfo")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = C.hex_rgba("#0d0c0b")
    mix.inputs["B"].default_value = C.hex_rgba("#4a3a2a")
    nt.links.new(info.outputs["Color"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    if "Sheen Weight" in b.inputs:            # soft rim from the windows
        b.inputs["Sheen Weight"].default_value = 0.6
    return mat


def hall_set(origin=(30, 0, 0), rows=7, per_row=11, collection=None, volume=True):
    """Returns dict with figures (in seating order), lights, and key points."""
    o = Vector(origin)
    col = collection or C.new_collection("HallSet")
    out = {"collection": col, "origin": o, "figures": []}
    floor_mat = M.wood("HallFloor")
    wall_mat = M.flat("HallWall", "#3a332b", roughness=0.85)
    P.box("HallFloor", (16, 18, 0.1), tuple(o + Vector((0, 0, -0.05))), col, floor_mat, bevel=0)
    P.box("HallBackWall", (16, 0.3, 7), tuple(o + Vector((0, 8.0, 3.5))), col, wall_mat, bevel=0)
    P.box("HallRearWall", (16, 0.3, 7), tuple(o + Vector((0, -9.0, 3.5))), col, wall_mat, bevel=0)
    P.box("HallRightWall", (0.3, 18, 7), tuple(o + Vector((7.5, 0, 3.5))), col, wall_mat, bevel=0)
    P.box("HallCeiling", (16, 18, 0.2), tuple(o + Vector((0, 0, 7.0))), col, wall_mat, bevel=0)
    # left wall with 5 tall window openings (gaps between piers)
    wx = -7.5
    ys = [-7.0, -4.0, -1.0, 2.0, 5.0]
    win_w, win_z0, win_z1 = 1.3, 1.2, 5.4
    edges = [-9.0] + [v for y in ys for v in (y - win_w / 2, y + win_w / 2)] + [8.0]
    for i in range(0, len(edges), 2):
        a, b = edges[i], edges[i + 1]
        P.box(f"HallPier{i}", (0.3, b - a, 7), tuple(o + Vector((wx, (a + b) / 2, 3.5))), col, wall_mat, bevel=0)
    for j, y in enumerate(ys):
        P.box(f"HallSill{j}", (0.3, win_w, win_z0), tuple(o + Vector((wx, y, win_z0 / 2))), col, wall_mat, bevel=0)
        P.box(f"HallHead{j}", (0.3, win_w, 7 - win_z1), tuple(o + Vector((wx, y, (7 + win_z1) / 2))), col,
              wall_mat, bevel=0)
        # mullions
        P.box(f"HallMullionV{j}", (0.06, 0.06, win_z1 - win_z0), tuple(o + Vector((wx, y, (win_z0 + win_z1) / 2))),
              col, wall_mat, bevel=0)
        P.box(f"HallMullionH{j}", (0.06, win_w, 0.06), tuple(o + Vector((wx, y, 3.6))), col, wall_mat, bevel=0)
    # bright sky cards outside the windows (seen through the openings)
    sky = M.emission("HallSky", "#dfe6ee", 3.0)
    P.box("HallSkyCard", (0.05, 20, 9), tuple(o + Vector((wx - 3.0, 0, 3.5))), col, sky, bevel=0)

    # presidium table (draped dark cloth) + papers
    P.box("PresidiumTable", (6.0, 1.1, 0.8), tuple(o + Vector((0, 5.6, 0.4))), col,
          M.flat("TableCloth", "#2a1714", 0.8), bevel=0.01)
    paper = M.flat("HallPapers", "#d9c7a3", 0.8)
    for k in range(7):
        P.box(f"HallPaper{k}", (0.3, 0.42, 0.004), tuple(o + Vector((-2.4 + k * 0.8, 5.5, 0.802))), col,
              paper, rot_z=math.radians(-8 + 5 * (k % 3)), bevel=0)

    # benches + 77 faceless figures (7 rows x 11, centre aisle)
    me = _figure_mesh()
    sil = silhouette_material()
    me.materials.append(sil)
    bench_mat = M.flat("Bench", "#24160d", 0.6)
    seat_dx = 0.78
    row_dy = 1.25
    for r in range(rows):
        y = 3.2 - r * row_dy
        for side in (-1, 1):
            n_side = per_row // 2 + (1 if side == 1 and per_row % 2 else 0)
            x0 = 0.8 * side
            length = n_side * seat_dx
            P.box(f"Bench_{r}_{side}", (length, 0.45, 0.45),
                  tuple(o + Vector((side * (0.8 + length / 2), y, 0.225))), col, bench_mat, bevel=0.01)
            for k in range(n_side):
                fig = bpy.data.objects.new(f"Delegate_{r:02d}_{side}_{k:02d}", me)
                fig.location = o + Vector((side * (0.8 + seat_dx * (k + 0.5)), y - 0.05, 0.0))
                fig.rotation_euler.z = math.radians((k % 3 - 1) * 4)
                fig.scale = (1, 1, 0.94 + 0.08 * ((r * 7 + k * 3) % 5) / 4)
                fig.color = (0.0, 0.0, 0.0, 1)
                C.link(fig, col)
                out["figures"].append(fig)
    out["front"] = o + Vector((0, 5.6, 1.0))

    if volume:
        vol = P.box("HallAir", (15.5, 17.5, 6.9), tuple(o + Vector((0, 0, 3.45))), col, None, bevel=0)
        vm = bpy.data.materials.new("HallHaze")
        vm.use_nodes = True
        nt = vm.node_tree
        nt.nodes.remove(nt.nodes["Principled BSDF"])
        pv = nt.nodes.new("ShaderNodeVolumePrincipled")
        pv.inputs["Density"].default_value = 0.035
        pv.inputs["Anisotropy"].default_value = 0.55
        nt.links.new(pv.outputs["Volume"], nt.nodes["Material Output"].inputs["Volume"])
        vol.data.materials.append(vm)
        out["volume"] = vol

    sun = bpy.data.lights.new("HallSun", "SUN")
    sun.color = C.kelvin_rgb(5200)
    sun.angle = math.radians(1.2)
    sun_obj = C.link(bpy.data.objects.new("HallSun", sun), col)
    sun_obj.rotation_euler = (math.radians(52), 0, math.radians(-62))   # in through the left windows
    out["sun"] = (sun_obj, sun)
    fill = bpy.data.lights.new("HallFill", "AREA")
    fill.size = 6
    fill.color = C.kelvin_rgb(3300)
    fill_obj = C.link(bpy.data.objects.new("HallFill", fill), col)
    fill_obj.location = o + Vector((3, 6.5, 6.5))
    C.look_at(fill_obj, tuple(o))
    out["fill"] = (fill_obj, fill)
    return out


# --------------------------------------------------------------------------
# Steppe (Scenes 02 and 08): rolling hills, wind grass, sky, silhouettes
# --------------------------------------------------------------------------
def sky_world(scene, sun_elev_deg=4.0, sun_rot_deg=95.0, strength=0.6, tint=None):
    w = scene.world
    nt = w.node_tree
    bg = nt.nodes["Background"]
    try:
        sky = nt.nodes.new("ShaderNodeTexSky")
        sky.sky_type = "NISHITA"
        sky.sun_elevation = math_rad(sun_elev_deg)
        sky.sun_rotation = math_rad(sun_rot_deg)
        sky.altitude = 1200
        sky.air_density = 1.4
        sky.dust_density = 2.5
        sky.sun_disc = True
        nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    except Exception as exc:  # older/newer API: fall back to a gradient
        print("[1617] sky fallback:", exc)
        bg.inputs["Color"].default_value = tint or C.hex_rgba("#d9a46a")
    bg.inputs["Strength"].default_value = strength
    return bg


def math_rad(d):
    return d * math.pi / 180.0


def _terrain_texture():
    tex = bpy.data.textures.get("SteppeHills") or bpy.data.textures.new("SteppeHills", "CLOUDS")
    tex.noise_scale = 160.0
    tex.noise_depth = 2
    return tex


def _displace(obj, strength=28.0):
    sub = obj.modifiers.new("Displace", "DISPLACE")
    sub.texture = _terrain_texture()
    sub.texture_coords = "GLOBAL"
    sub.strength = strength
    sub.mid_level = 0.5
    return sub


def _grid(name, size, subdiv, collection, mat):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=subdiv, y_segments=subdiv, size=size / 2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    obj = C.link(bpy.data.objects.new(name, me), collection)
    me.materials.append(mat)
    return obj


def ground_material(name="SteppeGround"):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.95
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 0.05
    n.inputs["Detail"].default_value = 8
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = C.hex_rgba("#5b5a2e")
    ramp.color_ramp.elements[1].color = C.hex_rgba("#a08a4c")
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return mat


def grass_material(name="SteppeGrass"):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.6
    b.inputs["Subsurface Weight"].default_value = 0.0
    info = nt.nodes.new("ShaderNodeObjectInfo")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = C.hex_rgba("#6b6a2a")
    ramp.color_ramp.elements[1].color = C.hex_rgba("#c9a85e")
    nt.links.new(info.outputs["Random"], ramp.inputs["Fac"])
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(ramp.outputs["Color"], tr.inputs["Color"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.35
    nt.links.new(b.outputs["BSDF"], mix.inputs[1])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
    return mat


def _grass_nodes(name, density, mat):
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    dist = N.new("GeometryNodeDistributePointsOnFaces")
    dist.inputs["Density"].default_value = density
    L.new(gi.outputs[0], dist.inputs["Mesh"])
    # a blade: tall thin triangle
    blade = N.new("GeometryNodeCurvePrimitiveLine")
    blade.inputs["Start"].default_value = (0, 0, 0)
    blade.inputs["End"].default_value = (0, 0.12, 0.6)
    prof = N.new("GeometryNodeCurvePrimitiveLine")
    prof.inputs["Start"].default_value = (-0.005, 0, 0)
    prof.inputs["End"].default_value = (0.005, 0, 0)
    sweep = N.new("GeometryNodeCurveToMesh")
    res = N.new("GeometryNodeResampleCurve")
    res.inputs["Count"].default_value = 4
    L.new(blade.outputs["Curve"], res.inputs["Curve"])
    L.new(res.outputs["Curve"], sweep.inputs["Curve"])
    L.new(prof.outputs["Curve"], sweep.inputs["Profile Curve"])
    taper = N.new("GeometryNodeSetCurveRadius")
    L.new(res.outputs["Curve"], taper.inputs["Curve"])
    par = N.new("GeometryNodeSplineParameter")
    inv = N.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    L.new(par.outputs["Factor"], inv.inputs[1])
    L.new(inv.outputs[0], taper.inputs["Radius"])
    L.new(taper.outputs["Curve"], sweep.inputs["Curve"])
    inst = N.new("GeometryNodeInstanceOnPoints")
    L.new(dist.outputs["Points"], inst.inputs["Points"])
    L.new(sweep.outputs["Mesh"], inst.inputs["Instance"])
    # random yaw + wind lean from a moving noise field
    rnd = N.new("FunctionNodeRandomValue")
    rnd.data_type = "FLOAT"
    rnd.inputs[2].default_value = 0.0
    rnd.inputs[3].default_value = 6.283
    t = N.new("GeometryNodeInputSceneTime")
    pos = N.new("GeometryNodeInputPosition")
    off = N.new("ShaderNodeVectorMath")
    off.operation = "SCALE"
    L.new(t.outputs["Seconds"], off.inputs["Scale"])
    off.inputs[0].default_value = (1.6, 0.4, 0.0)       # gusts travel along +X
    addp = N.new("ShaderNodeVectorMath")
    addp.operation = "SUBTRACT"
    L.new(pos.outputs["Position"], addp.inputs[0])
    L.new(off.outputs[0], addp.inputs[1])
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.12
    L.new(addp.outputs[0], nz.inputs["Vector"])
    lean = N.new("ShaderNodeMath")
    lean.operation = "MULTIPLY"
    lean.inputs[1].default_value = 0.9
    L.new(nz.outputs["Fac"], lean.inputs[0])
    comb = N.new("ShaderNodeCombineXYZ")
    L.new(lean.outputs[0], comb.inputs["X"])
    L.new(rnd.outputs[1], comb.inputs["Z"])
    L.new(comb.outputs["Vector"], inst.inputs["Rotation"])
    sc = N.new("FunctionNodeRandomValue")
    sc.data_type = "FLOAT"
    sc.inputs[2].default_value = 0.5
    sc.inputs[3].default_value = 1.4
    sc.inputs["Seed"].default_value = 5
    L.new(sc.outputs[1], inst.inputs["Scale"])
    setm = N.new("GeometryNodeSetMaterial")
    setm.inputs["Material"].default_value = mat
    L.new(inst.outputs["Instances"], setm.inputs["Geometry"])
    join = N.new("GeometryNodeJoinGeometry")
    L.new(setm.outputs["Geometry"], join.inputs[0])
    L.new(gi.outputs[0], join.inputs[0])
    L.new(join.outputs[0], go.inputs[0])
    return ng


def figure_silhouette_mesh(kind="rider"):
    """Low-poly horse + rider (or standing person) silhouette, faceless."""
    import bmesh
    from mathutils import Matrix
    bm = bmesh.new()

    def blob(r, scale, loc, rot=None):
        g = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=7, radius=r)
        bmesh.ops.scale(bm, vec=scale, verts=g["verts"])
        if rot:
            bmesh.ops.rotate(bm, verts=g["verts"], cent=(0, 0, 0), matrix=rot)
        bmesh.ops.translate(bm, verts=g["verts"], vec=loc)

    def limb(r, length, loc, tilt=0.0):
        g = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=r * 0.7, depth=length)
        bmesh.ops.rotate(bm, verts=g["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(tilt, 3, "X"))
        bmesh.ops.translate(bm, verts=g["verts"], vec=loc)

    if kind == "rider":
        blob(1.0, (0.32, 0.85, 0.36), (0, 0, 1.35))                                    # barrel
        blob(1.0, (0.15, 0.40, 0.17), (0, 0.90, 1.78), Matrix.Rotation(0.75, 3, "X"))   # neck, up-forward
        blob(1.0, (0.11, 0.30, 0.12), (0, 1.22, 2.02), Matrix.Rotation(-0.9, 3, "X"))   # head, nose down
        for x in (-0.16, 0.16):
            for y, tl in ((0.55, 0.12), (-0.55, -0.12)):
                limb(0.06, 1.05, (x, y, 0.55), tl)
        blob(1.0, (0.07, 0.30, 0.07), (0, -0.95, 1.25), Matrix.Rotation(0.7, 3, "X"))   # tail
        blob(1.0, (0.20, 0.16, 0.36), (0, -0.05, 2.05))                                 # rider torso
        blob(0.13, (1, 1, 1.1), (0, -0.02, 2.55))                                       # head
        g = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.17, radius2=0.02, depth=0.2)
        bmesh.ops.translate(bm, verts=g["verts"], vec=(0, -0.02, 2.72))                 # hat
    else:
        blob(1.0, (0.24, 0.18, 0.55), (0, 0, 1.05))
        blob(0.13, (1, 1, 1.1), (0, 0, 1.72))
        g = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.36, radius2=0.2, depth=0.9)
        bmesh.ops.translate(bm, verts=g["verts"], vec=(0, 0, 0.45))                     # deel skirt
    me = bpy.data.meshes.new(f"Silhouette_{kind}")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me


def ger(name, location, collection, radius=3.0, mat=None, roof_mat=None):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=radius, radius2=radius, depth=1.7)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.85))
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=radius * 1.04, radius2=radius * 0.18,
                              depth=1.1)
    bmesh.ops.translate(bm, verts=r["verts"], vec=(0, 0, 2.25))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = C.link(bpy.data.objects.new(name, me), collection)
    obj.location = location
    me.materials.append(mat or M.flat("Felt", "#d8cdb6", 0.95))
    return obj


def steppe_set(collection=None, grass_center=(0, 0), grass_size=70, grass_density=12, hills=28.0):
    col = collection or C.new_collection("Steppe")
    out = {"collection": col}
    gmat = ground_material()
    terrain = _grid("Terrain", 4000, 220, col, gmat)
    _displace(terrain, hills)
    terrain.location.z = -hills * 0.5
    patch = _grid("GrassPatch", grass_size, 70, col, gmat)
    patch.location = (grass_center[0], grass_center[1], -hills * 0.5 + 0.02)
    _displace(patch, hills)
    gn = patch.modifiers.new("Grass", "NODES")
    gn.node_group = _grass_nodes("GrassGN", grass_density, grass_material())
    out["terrain"], out["patch"] = terrain, patch
    out["ground_z"] = lambda x, y: ground_height(terrain, x, y)
    return out


def ground_height(terrain, x, y):
    """Height of the displaced terrain at (x, y): ray-cast the evaluated mesh."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = terrain.evaluated_get(dg)
    inv = terrain.matrix_world.inverted()
    origin = inv @ Vector((x, y, 1000.0))
    direction = (inv.to_3x3() @ Vector((0, 0, -1))).normalized()
    hit, loc, _n, _i = ev.ray_cast(origin, direction)
    return (terrain.matrix_world @ loc).z if hit else 0.0
