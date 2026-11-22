"""Procedural props: parchment sheet, 1920s pocket watch, chain, ribbon,
desk dressing and a geometry-nodes dust field. All geometry is built in
code (no downloaded models) so licensing is trivially 'self-created'."""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

from . import materials as M
from .common import link, smooth, text_object


def _obj_from_bm(name, bm, collection=None, mat=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    if mat:
        me.materials.append(mat)
    return link(obj, collection)


# --------------------------------------------------------------------------
# Parchment
# --------------------------------------------------------------------------
def parchment_sheet(name, size=(0.297, 0.42), res=(150, 212), mat=None, collection=None,
                    seed=7, curl=1.0):
    """A sheet with a centre fold, lifted/curled corners and soft waviness."""
    sx, sy = size
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    nx, ny = res
    verts = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            u, v = i / nx, j / ny
            x, y = (u - 0.5) * sx, (v - 0.5) * sy
            row.append(bm.verts.new((x, y, 0.0)))
        verts.append(row)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
            for loop, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uv_layer].uv = (ii / nx, jj / ny)

    off = Vector((seed * 1.37, seed * 2.11, seed * 0.73))
    corner_lift = {(1, -1): 0.018, (-1, -1): 0.006, (1, 1): 0.009, (-1, 1): 0.004}
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        u, w = x / (sx / 2), y / (sy / 2)              # -1..1
        z = 0.0
        # centre fold (sheet was once folded in half): soft tent ridge
        z += 0.0035 * curl * max(0.0, 1.0 - abs(w)) ** 1.6
        # edge curl, strongest at the corners
        for (cu, cw), amt in corner_lift.items():
            d = max(0.0, (u * cu + w * cw) - 1.25) / 0.75
            z += amt * curl * d * d
        de = min(1 - abs(u), 1 - abs(w))
        z += 0.0025 * curl * max(0.0, 0.10 - de) / 0.10 * (0.5 + noise.noise(Vector((x, y, 0)) * 9 + off))
        # gentle cockling of old paper
        z += 0.0012 * noise.noise(Vector((x * 14, y * 14, 0.3)) + off)
        z += 0.0004 * noise.noise(Vector((x * 45, y * 45, 0.7)) + off)
        v.co.z = max(0.0, z + 0.0012)
    obj = _obj_from_bm(name, bm, collection, mat)
    smooth(obj, 60)
    sol = obj.modifiers.new("Thickness", "SOLIDIFY")
    sol.thickness = 0.00035
    sol.offset = -1
    return obj


# --------------------------------------------------------------------------
# Pocket watch
# --------------------------------------------------------------------------
WATCH_R = 0.026
DIAL_Z = 0.0090


def _spin_profile(name, profile, steps=128, collection=None, mat=None):
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0.0, z)) for r, z in profile]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=2 * math.pi, steps=steps, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    obj = _obj_from_bm(name, bm, collection, mat)
    smooth(obj, 50)
    return obj


def _flat_poly(name, pts, thickness, collection=None, mat=None, z=0.0):
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z)) for x, y in pts]
    f = bm.faces.new(vs)
    ret = bmesh.ops.extrude_face_region(bm, geom=[f])
    moved = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=moved, vec=(0, 0, thickness))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj_from_bm(name, bm, collection, mat)


def _hand_outline(length, width, tail=0.0, tip="lance", hub=0.0011):
    """Hand outline pointing to +Y, hub at the origin."""
    pts = []
    if tip == "spade":
        pts = [(-width * 0.35, -tail), (-width * 0.35, length * 0.55), (-width, length * 0.72),
               (-width * 0.2, length * 0.86), (0.0, length), (width * 0.2, length * 0.86),
               (width, length * 0.72), (width * 0.35, length * 0.55), (width * 0.35, -tail)]
    elif tip == "lance":
        pts = [(-width * 0.5, -tail), (-width * 0.5, length * 0.8), (0.0, length),
               (width * 0.5, length * 0.8), (width * 0.5, -tail)]
    else:  # needle with counterweight
        pts = [(-width * 1.6, -tail), (-width * 0.4, -tail * 0.4), (-width * 0.4, length * 0.9),
               (0.0, length), (width * 0.4, length * 0.9), (width * 0.4, -tail * 0.4),
               (width * 1.6, -tail)]
    return pts  # the hub is covered by the centre cap


def pocket_watch(name, fonts, collection=None):
    """Returns dict with root empty and the three hand objects.

    Dial carries 1–12 plus an inner 13–24 ring in red, as many early
    20th-century pocket watches did, so 16:17 is readable on a 12h dial."""
    brass = M.metal("Brass", "#C8A56C", roughness=0.22)
    brass_dark = M.metal("BrassDark", "#A46A3A", roughness=0.35)
    steel_blue = M.metal("BluedSteel", "#1b2a4a", roughness=0.18, wear=False)
    crimson = M.flat("CrimsonPaint", "#782E2F", roughness=0.35, coat=0.5)
    ink = M.flat("DialInk", "#141210", roughness=0.4)
    red_ink = M.flat("DialRed", "#8a2a26", roughness=0.4)
    dial_mat = M.enamel()
    glass = M.glass()

    root = bpy.data.objects.new(name, None)
    root.empty_display_size = 0.03
    link(root, collection)

    def parent(o):
        o.parent = root
        return o

    case_profile = [(0.0, 0.0), (0.008, 0.00015), (0.014, 0.0005), (0.019, 0.0011),
                    (0.0228, 0.0021), (0.0252, 0.0036), (0.0262, 0.0052), (0.0263, 0.0070),
                    (0.0259, 0.0086), (0.0251, 0.0098), (0.0241, 0.0106), (0.0233, 0.0107),
                    (0.0229, 0.0101), (0.0229, DIAL_Z - 0.0002)]
    parent(_spin_profile(f"{name}_Case", case_profile, collection=collection, mat=brass))
    # decorative engraved groove ring on the band
    groove = [(0.02635, 0.0058), (0.0258, 0.0061), (0.02635, 0.0064)]
    parent(_spin_profile(f"{name}_Groove", groove, collection=collection, mat=brass_dark))

    # dial
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=False, segments=128, radius=0.0229)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, DIAL_Z))
    parent(_obj_from_bm(f"{name}_Dial", bm, collection, dial_mat))

    # minute track + hour markers (one mesh)
    bm = bmesh.new()
    for k in range(60):
        a = -k * math.tau / 60
        major = k % 5 == 0
        w, l = (0.00055, 0.0021) if major else (0.00018, 0.0011)
        r = 0.0212 - l / 2
        m = (Matrix.Translation((0, 0, DIAL_Z + 0.00003)) @ Matrix.Rotation(a, 4, "Z")
             @ Matrix.Translation((0, r, 0)) @ Matrix.Diagonal((w, l, 0.00004, 1)))
        bmesh.ops.create_cube(bm, size=1.0, matrix=m)
    # outer and inner rings of the railway track
    for rr in (0.0219, 0.0204):
        ring = bmesh.ops.create_circle(bm, cap_ends=False, segments=128, radius=rr)
        bmesh.ops.translate(bm, verts=ring["verts"], vec=(0, 0, DIAL_Z + 0.00003))
    me_obj = parent(_obj_from_bm(f"{name}_Track", bm, collection, ink))
    me_obj.modifiers.new("ring", "WIREFRAME").thickness = 0.00012
    me_obj.modifiers["ring"].use_replace = False

    # numerals
    for h in range(1, 13):
        a = math.radians(90 - h * 30)
        t = text_object(f"{name}_N{h}", str(h), fonts["serif"], size=0.0047,
                        collection=collection,
                        location=(0.0168 * math.cos(a), 0.0168 * math.sin(a), DIAL_Z + 0.00004))
        t.data.materials.append(ink)
        parent(t)
        t2 = text_object(f"{name}_R{h + 12}", str(h + 12), fonts["sans"], size=0.0019,
                         collection=collection,
                         location=(0.0118 * math.cos(a), 0.0118 * math.sin(a), DIAL_Z + 0.00004))
        t2.data.materials.append(red_ink)
        parent(t2)

    # hands
    hour = parent(_flat_poly(f"{name}_HourHand", _hand_outline(0.0112, 0.0019, 0.0016, "spade"),
                             0.00022, collection, steel_blue, z=DIAL_Z + 0.0002))
    minute = parent(_flat_poly(f"{name}_MinuteHand", _hand_outline(0.0178, 0.0011, 0.002, "lance"),
                               0.0002, collection, steel_blue, z=DIAL_Z + 0.00045))
    second = parent(_flat_poly(f"{name}_SecondHand", _hand_outline(0.0195, 0.00028, 0.0055, "needle"),
                               0.00015, collection, crimson, z=DIAL_Z + 0.00068))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.0009, radius2=0.0007, depth=0.0011)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, DIAL_Z + 0.0007))
    parent(_obj_from_bm(f"{name}_Cap", bm, collection, brass))

    # crystal: shallow dome
    dome = [(0.0233, 0.0104)]
    for k in range(1, 17):
        r = 0.0233 * (1 - k / 16)
        dome.append((r, 0.0104 + 0.0024 * (1 - (r / 0.0233) ** 2)))
    # single surface on purpose (thin-glass shader); a solidified shell traps rays
    parent(_spin_profile(f"{name}_Crystal", dome, collection=collection, mat=glass))

    # pendant, crown (knurled) and bow at 12 o'clock
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.0021, radius2=0.0017, depth=0.004)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0.0275, 0.0060))
    parent(_obj_from_bm(f"{name}_Pendant", bm, collection, brass))
    bm = bmesh.new()
    star = [((0.0034 if k % 2 == 0 else 0.0030) * math.cos(k * math.tau / 48),
             (0.0034 if k % 2 == 0 else 0.0030) * math.sin(k * math.tau / 48)) for k in range(48)]
    vs = [bm.verts.new((x, y, -0.0022)) for x, y in star]
    f = bm.faces.new(vs)
    ret = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, verts=[e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)],
                        vec=(0, 0, 0.0044))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0.0315, 0.0060))
    parent(_obj_from_bm(f"{name}_Crown", bm, collection, brass))
    bm = bmesh.new()
    _torus(bm, 0.0068, 0.00095, 48, 12)
    bmesh.ops.scale(bm, vec=(1.0, 0.8, 1.0), verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(-14), 3, "X"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0.0352, 0.0032))
    bow = parent(_obj_from_bm(f"{name}_Bow", bm, collection, brass))
    smooth(bow, 80)
    return {"root": root, "hour": hour, "minute": minute, "second": second}


def _torus(bm, R, r, seg_major, seg_minor):
    rings = []
    for i in range(seg_major):
        a = i * math.tau / seg_major
        ring = []
        for j in range(seg_minor):
            b = j * math.tau / seg_minor
            ring.append(bm.verts.new(((R + r * math.cos(b)) * math.cos(a),
                                      (R + r * math.cos(b)) * math.sin(a),
                                      r * math.sin(b))))
        rings.append(ring)
    for i in range(seg_major):
        for j in range(seg_minor):
            a, b = rings[i], rings[(i + 1) % seg_major]
            bm.faces.new((a[j], b[j], b[(j + 1) % seg_minor], a[(j + 1) % seg_minor]))


def chain(name, points, collection=None, mat=None, pitch=0.0046):
    """Curb chain: alternating flat/upright links arrayed along a curve."""
    cu = bpy.data.curves.new(f"{name}_Path", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    path = link(bpy.data.objects.new(f"{name}_Path", cu), collection)

    bm = bmesh.new()
    _torus(bm, 0.0026, 0.00055, 24, 8)
    bmesh.ops.scale(bm, vec=(1.45, 1.0, 1.0), verts=bm.verts)
    bm2 = bmesh.new()
    _torus(bm2, 0.0026, 0.00055, 24, 8)
    bmesh.ops.scale(bm2, vec=(1.45, 1.0, 1.0), verts=bm2.verts)
    bmesh.ops.rotate(bm2, verts=bm2.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    bmesh.ops.translate(bm2, verts=bm2.verts, vec=(pitch, 0, 0.0026))
    me2 = bpy.data.meshes.new("tmp")
    bm2.to_mesh(me2)
    bm2.free()
    bm.from_mesh(me2)
    bpy.data.meshes.remove(me2)
    links = _obj_from_bm(name, bm, collection, mat)
    smooth(links, 80)
    arr = links.modifiers.new("Array", "ARRAY")
    arr.fit_type = "FIT_CURVE"
    arr.curve = path
    arr.use_relative_offset = False
    arr.use_constant_offset = True
    arr.constant_offset_displace = (2 * pitch, 0, 0)
    cm = links.modifiers.new("Curve", "CURVE")
    cm.object = path
    cm.deform_axis = "POS_X"
    return links, path


def ribbon(name, points, width=0.012, collection=None, mat=None, twist=0.0):
    """Flat silk ribbon following a polyline (Catmull-Rom smoothed)."""
    pts = [Vector(p) for p in points]
    samples = []
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        for k in range(12):
            t = k / 12
            samples.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                  + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    samples.append(pts[-1])
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    left, right = [], []
    for i, p in enumerate(samples):
        d = (samples[min(i + 1, len(samples) - 1)] - samples[max(i - 1, 0)]).normalized()
        n = Vector((-d.y, d.x, 0)).normalized()
        tw = twist * math.sin(i * 0.15)
        off = n * (width / 2)
        left.append(bm.verts.new(p + off + Vector((0, 0, max(0, tw) * width))))
        right.append(bm.verts.new(p - off + Vector((0, 0, max(0, -tw) * width))))
    for i in range(len(samples) - 1):
        f = bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
        for loop, c in zip(f.loops, ((0, i), (1, i), (1, i + 1), (0, i + 1))):
            loop[uv].uv = (c[0], c[1] / len(samples))
    obj = _obj_from_bm(name, bm, collection, mat)
    smooth(obj, 80)
    obj.modifiers.new("t", "SOLIDIFY").thickness = 0.0003
    return obj


def box(name, size, location, collection=None, mat=None, rot_z=0.0, bevel=0.002):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((*size, 1)))
    obj = _obj_from_bm(name, bm, collection, mat)
    obj.location = location
    obj.rotation_euler.z = rot_z
    if bevel:
        b = obj.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = 2
    return obj


def cylinder(name, radius, depth, location, collection=None, mat=None, segments=48):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius, radius2=radius, depth=depth)
    obj = _obj_from_bm(name, bm, collection, mat)
    obj.location = location
    smooth(obj, 40)
    return obj


# --------------------------------------------------------------------------
# Dust field (Geometry Nodes, deterministic per frame -> safe for any render order)
# --------------------------------------------------------------------------
def dust_field(name, bounds_min, bounds_max, count=1400, radius=(0.00012, 0.00045),
               drift=(0.0004, 0.0002, 0.0012), wander=0.006, collection=None, mat=None, seed=3):
    ng = bpy.data.node_groups.new(f"{name}_GN", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gin = N.new("NodeGroupInput")
    gout = N.new("NodeGroupOutput")

    rnd = N.new("FunctionNodeRandomValue")
    rnd.data_type = "FLOAT_VECTOR"
    rnd.inputs[0].default_value = bounds_min
    rnd.inputs[1].default_value = bounds_max
    rnd.inputs["Seed"].default_value = seed
    pts = N.new("GeometryNodePoints")
    pts.inputs["Count"].default_value = count
    L.new(rnd.outputs[0], pts.inputs["Position"])

    t = N.new("GeometryNodeInputSceneTime")
    pos = N.new("GeometryNodeInputPosition")
    nz = N.new("ShaderNodeTexNoise")
    nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value = 18.0
    nz.inputs["Detail"].default_value = 1.0
    wmul = N.new("ShaderNodeMath")
    wmul.operation = "MULTIPLY"
    wmul.inputs[1].default_value = 0.08
    L.new(t.outputs["Seconds"], wmul.inputs[0])
    L.new(pos.outputs["Position"], nz.inputs["Vector"])
    L.new(wmul.outputs[0], nz.inputs["W"])
    centre = N.new("ShaderNodeVectorMath")
    centre.operation = "SUBTRACT"
    centre.inputs[1].default_value = (0.5, 0.5, 0.5)
    L.new(nz.outputs["Color"], centre.inputs[0])
    amp = N.new("ShaderNodeVectorMath")
    amp.operation = "SCALE"
    amp.inputs["Scale"].default_value = wander
    L.new(centre.outputs[0], amp.inputs[0])
    dr = N.new("ShaderNodeVectorMath")
    dr.operation = "SCALE"
    dr.inputs[0].default_value = drift
    L.new(t.outputs["Seconds"], dr.inputs["Scale"])
    add = N.new("ShaderNodeVectorMath")
    add.operation = "ADD"
    L.new(amp.outputs[0], add.inputs[0])
    L.new(dr.outputs[0], add.inputs[1])
    setp = N.new("GeometryNodeSetPosition")
    L.new(pts.outputs["Points"], setp.inputs["Geometry"])
    L.new(add.outputs[0], setp.inputs["Offset"])

    ico = N.new("GeometryNodeMeshIcoSphere")
    ico.inputs["Radius"].default_value = 1.0
    ico.inputs["Subdivisions"].default_value = 1
    rs = N.new("FunctionNodeRandomValue")
    rs.data_type = "FLOAT"
    rs.inputs[2].default_value = radius[0]
    rs.inputs[3].default_value = radius[1]
    rs.inputs["Seed"].default_value = seed + 11
    # skew sizes: many tiny motes, few larger fibres
    pw = N.new("ShaderNodeMath")
    pw.operation = "POWER"
    L.new(rs.outputs[1], pw.inputs[0])
    pw.inputs[1].default_value = 1.0
    inst = N.new("GeometryNodeInstanceOnPoints")
    L.new(setp.outputs["Geometry"], inst.inputs["Points"])
    L.new(ico.outputs["Mesh"], inst.inputs["Instance"])
    L.new(pw.outputs[0], inst.inputs["Scale"])
    setm = N.new("GeometryNodeSetMaterial")
    setm.inputs["Material"].default_value = mat
    L.new(inst.outputs["Instances"], setm.inputs["Geometry"])
    L.new(setm.outputs["Geometry"], gout.inputs[0])

    me = bpy.data.meshes.new(name)
    obj = link(bpy.data.objects.new(name, me), collection)
    mod = obj.modifiers.new("Dust", "NODES")
    mod.node_group = ng
    return obj


def animate_watch(watch, hit_frame, f_start, f_end, fps=24, hms=(16, 17, 0)):
    """Real-time clockwork: second hand dead-beats once per second (tiny
    recoil), minute/hour hands creep; reads exactly `hms` at hit_frame."""
    from .common import key, set_interpolation
    t_hit = hms[0] * 3600 + hms[1] * 60 + hms[2]
    for f in range(f_start, f_end + 1):
        t = t_hit + (f - hit_frame) / fps
        whole = math.floor(t)
        frac = t - whole
        if frac < 0.06:
            step = frac / 0.06 * 1.08
        elif frac < 0.14:
            step = 1.08 - (frac - 0.06) / 0.08 * 0.08
        else:
            step = 1.0
        sec_angle = ((whole - 1 + step) % 60) / 60 * math.tau
        key(watch["second"], "rotation_euler", f, -sec_angle, index=2)
        key(watch["minute"], "rotation_euler", f, -((t / 60.0) % 60) / 60 * math.tau, index=2)
        key(watch["hour"], "rotation_euler", f, -((t / 3600.0) % 12) / 12 * math.tau, index=2)
    for h in ("second", "minute", "hour"):
        set_interpolation(watch[h], "LINEAR")


def page_stack(name, n, size, mats, location, collection=None, rot_z=0.0, dz=0.00045):
    """n thin sheets whose origin sits on their LEFT edge (the spine), so
    they can be turned with rotation_euler.y plus a bend modifier."""
    pages = []
    for i in range(n):
        pg = parchment_sheet(f"{name}{i:02d}", size=size, res=(36, 50), mat=mats[i % len(mats)],
                             collection=collection, seed=40 + i, curl=0.15)
        for v in pg.data.vertices:
            v.co.x += size[0] / 2
        pg.modifiers["Thickness"].thickness = 0.00025
        bend = pg.modifiers.new("Curl", "SIMPLE_DEFORM")
        bend.deform_method = "BEND"
        bend.deform_axis = "Y"
        bend.angle = 0.0
        pg.location = (location[0], location[1], location[2] + (n - i) * dz)
        pg.rotation_euler.z = rot_z
        pages.append(pg)            # pages[0] is the top sheet
    return pages
