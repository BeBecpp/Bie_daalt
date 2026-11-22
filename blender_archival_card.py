"""Blender bpy integration for 16:17's real archival photo cards.

Import this from an existing Blender Python scene script. Do not represent these cards as
actual motion footage. Source photograph is textured onto a physically positioned plane.

    from blender_archival_card import add_archive_photo, verified_asset
    path = verified_asset('s04_revolutionaries_1921.jpg')
    if path:
        add_archive_photo(path, name='1921 Revolutionaries', start_frame=1, end_frame=144)

Opening scene/render settings are deliberately NOT reset by this helper.
"""
from __future__ import annotations
from pathlib import Path

ASSETS = Path(__file__).resolve().parent / 'assets' / 'archival'


def verified_asset(filename: str):
    """Existing valid image path or None. HTML 429 body is never accepted."""
    if Path(filename).name != filename:
        raise ValueError('filename must be a basename')
    p = ASSETS / filename
    if not p.is_file():
        return None
    data = p.read_bytes()
    if len(data) < 1024:
        return None
    if p.suffix.lower() == '.jpg' and not (data[:3] == b'\xff\xd8\xff' and data.rstrip().endswith(b'\xff\xd9')):
        return None
    if p.suffix.lower() == '.png' and not data.startswith(b'\x89PNG\r\n\x1a\n'):
        return None
    if p.suffix.lower() not in {'.jpg', '.png'}:
        return None
    return p


def add_archive_photo(path, *, name, start_frame=1, end_frame=144, target_width=7.0,
                      location=(0.0, 0.0, 0.0), tilt_deg=-4.0):
    """Textured 3D photo plane with a restrained camera-facing parallax drift."""
    import bpy
    import math
    from mathutils import Vector

    path = Path(path)
    good = verified_asset(path.name)
    if good is None or good.resolve() != path.resolve():
        raise ValueError('Archive asset does not exist or is not a verified JPEG/PNG: ' + str(path))
    img = bpy.data.images.load(str(good), check_existing=True)
    ratio = img.size[0] / max(1, img.size[1])
    mat = bpy.data.materials.new(name + ' / archive texture')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    photo = nodes.new('ShaderNodeTexImage')
    photo.image = img
    photo.interpolation = 'Linear'
    mat.node_tree.links.new(photo.outputs['Color'], principled.inputs['Base Color'])
    mat.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    bpy.ops.mesh.primitive_plane_add(size=2, location=location)
    plane = bpy.context.object
    plane.name = name
    plane.scale = (target_width / 2, (target_width / ratio) / 2, 1)
    plane.data.materials.append(mat)
    plane.rotation_euler[2] = math.radians(tilt_deg)
    plane.keyframe_insert(data_path='rotation_euler', frame=start_frame)
    plane.location.x = location[0] + .18
    plane.location.y = location[1] + .08
    plane.keyframe_insert(data_path='location', frame=start_frame)
    plane.location.x = location[0] - .18
    plane.location.y = location[1] - .08
    plane.keyframe_insert(data_path='location', frame=end_frame)
    plane.rotation_euler[2] = math.radians(-tilt_deg / 2)
    plane.keyframe_insert(data_path='rotation_euler', frame=end_frame)
    for fc in plane.animation_data.action.fcurves:
        for kf in fc.keyframe_points:
            kf.interpolation = 'BEZIER'
    return plane
