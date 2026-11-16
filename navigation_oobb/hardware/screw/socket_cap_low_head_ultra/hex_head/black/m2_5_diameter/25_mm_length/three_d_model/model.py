"""Parametric screw surface solids. Coordinates are millimetres, tip z=0.

This file is also copied to each generated folder as standalone model.py.
The full variant uses a right-handed, single-start, 60 degree external thread
with P/8 crest land and a tangent circular root of radius H/6.
"""
import argparse
import copy
import json
import math
from pathlib import Path

import numpy as np
import trimesh


def resolve_thread(parameters):
    """Resolve derived coordinates, including after a standalone length edit."""
    p = copy.deepcopy(parameters)
    d, length, pitch = p['diameter_mm'], p['length_mm'], p['pitch_mm']
    h = math.sqrt(3)/2*pitch
    p.update(thread_pitch_diameter_mm=d-3*h/4,
             thread_minor_diameter_mm=d-2*17*h/24,
             thread_root_radius_mm=h/6, thread_flank_angle_deg=60.)
    radius = p['underhead_fillet_mm']
    style = p.get('head_style', 'countersunk')
    if style == 'countersunk':
        half_angle = math.radians(p['countersink_angle_deg']/2)
        intersection = length-p['head_rim_mm']-(p['head_diameter_mm']-d)/2/math.tan(half_angle)
        tangent = intersection-radius*math.tan(half_angle/2)
        top = length
        contact = length-p['head_rim_mm']
    elif style == 'headless':
        top = length
        contact = length*.65
        tangent = length
    elif style in {'cylindrical', 'button', 'pan'}:
        tangent = length-radius
        top = length+p['head_height_mm']
        contact = length
    else:
        raise ValueError(f'Unsupported head style {style!r}')
    p.update(head_top_z_mm=top, overall_length_mm=top,
             head_contact_min_z_mm=contact)
    p['fillet_start_z_mm'] = tangent
    threshold = p['partial_thread_from_length_mm']
    partial = threshold is not None and length >= threshold
    coverage = p.get('thread_coverage', 'standard_reference')
    if coverage == 'full':
        partial = False
    elif coverage == 'partial':
        partial = True
    elif coverage != 'standard_reference':
        raise ValueError('thread_coverage must be standard_reference, full or partial')
    if partial and (p['thread_length_reference_mm'] is None or p['thread_length_reference_mm']+pitch >= tangent):
        raise ValueError('Partial thread length does not leave room for a shank')
    end = min(p['thread_length_reference_mm']+pitch, tangent) if partial else tangent
    p['thread_end_z_mm'] = end
    p['thread_runout_mm'] = min(pitch, end/3)
    p['thread_length_mm'] = end-p['thread_runout_mm']
    p['thread_mode'] = 'partial' if partial else 'full_to_head'
    p['grip_length_mm'] = length-p['thread_length_mm']
    p['shank_length_min_mm'] = max(0, p['grip_length_mm']-5*pitch) if partial else 0
    if style == 'headless':
        p.update(thread_mode='full_to_end', thread_end_z_mm=length,
                 thread_length_mm=length, grip_length_mm=0., thread_runout_mm=0.)
    return p


def validate_parameters(p):
    style = p.get('head_style', 'countersunk')
    keys = ['diameter_mm', 'length_mm', 'pitch_mm', 'tip_chamfer_mm']
    keys += (['socket_across_flats_mm', 'socket_depth_mm', 'cup_diameter_mm', 'cup_land_mm'] if style == 'headless' else
             ['head_diameter_mm', 'head_height_mm', 'underhead_fillet_mm'])
    for key in keys:
        value = p[key]
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f'{key} must be finite and positive')
    if p['handedness'] != 'right' or p['thread_starts'] != 1:
        raise ValueError('Only single-start right-handed threads are implemented')
    if style == 'headless':
        if not 0 < p['cup_diameter_mm'] < p['diameter_mm'] or not 90 <= p['cup_angle_deg'] <= 120:
            raise ValueError('Invalid cup point diameter or angle')
        inner = p['cup_diameter_mm']/2-p['cup_land_mm']
        cup_depth = inner/math.tan(math.radians(p['cup_angle_deg']/2))
        if inner <= 0 or cup_depth+p['socket_depth_mm'] >= p['length_mm']:
            raise ValueError('Cup and socket overlap; this short catalogue length needs a supplier drawing')
        if p['socket_across_flats_mm']/math.sqrt(3) >= p['thread_minor_diameter_mm']/2:
            raise ValueError('Socket does not fit the set-screw end face')
        if p['tip_chamfer_mm'] >= p['length_mm']/2 or p['pitch_mm'] >= p['diameter_mm']:
            raise ValueError('Invalid set screw thread or point envelope')
        return
    if p['head_diameter_mm'] <= p['diameter_mm']:
        raise ValueError('Head must be wider than shaft')
    if style == 'countersunk':
        if not 60 <= p['countersink_angle_deg'] <= 120 or p['head_rim_mm'] <= 0:
            raise ValueError('Invalid countersink angle or rim')
        cone_height = p['head_rim_mm']+(p['head_diameter_mm']-p['diameter_mm'])/2/math.tan(
            math.radians(p['countersink_angle_deg']/2))
        complete_head_height = cone_height+p['underhead_fillet_mm']*math.tan(
            math.radians(p['countersink_angle_deg']/4))
        if complete_head_height > p['head_height_mm']+1e-7:
            raise ValueError('Cone, rim and fillet exceed the specified maximum head height')
    elif style == 'cylindrical':
        if not 0 < p['head_edge_chamfer_mm'] < p['head_height_mm']/2:
            raise ValueError('Invalid cylindrical head chamfer')
    elif style == 'button':
        if not 0 < p['head_rim_mm'] < p['head_height_mm']:
            raise ValueError('Invalid domed head rim')
    elif style == 'pan':
        radius = p['head_crown_radius_mm']
        if radius <= p['head_diameter_mm']/2 or radius-math.sqrt(radius**2-(p['head_diameter_mm']/2)**2) >= p['head_height_mm']:
            raise ValueError('Pan crown does not leave a cylindrical skirt')
    if p['tip_chamfer_mm'] >= p['diameter_mm']/2:
        raise ValueError('Tip chamfer must leave a positive end face')
    if p.get('recess_type') in {'H', 'Z'}:
        for key in ('recess_diameter_mm', 'recess_depth_mm', 'recess_wing_width_mm', 'recess_core_width_mm'):
            if not isinstance(p[key], (int, float)) or not math.isfinite(p[key]) or p[key] <= 0:
                raise ValueError(f'{key} must be finite and positive')
        if p['recess_diameter_mm'] >= p['head_diameter_mm']:
            raise ValueError('Cross recess must fit inside head')
        depth = p['recess_depth_mm']
    else:
        for key in ('socket_across_flats_mm', 'socket_depth_mm'):
            if not isinstance(p[key], (int, float)) or not math.isfinite(p[key]) or p[key] <= 0:
                raise ValueError(f'{key} must be finite and positive')
        if p['socket_across_flats_mm']/math.sqrt(3) >= p['head_diameter_mm']/2:
            raise ValueError('Socket must fit inside head')
        depth = p['socket_depth_mm']
    if depth >= p['head_top_z_mm']-p['tip_chamfer_mm']:
        raise ValueError('Recess would break through the tip')
    if p['diameter_mm'] <= 2*17/24*math.sqrt(3)/2*p['pitch_mm']:
        raise ValueError('Thread root diameter must be positive')
    if p['fillet_start_z_mm'] <= p['tip_chamfer_mm']+p['pitch_mm']:
        raise ValueError('Length is too short for head, chamfer and thread')
    if not 0 < p['thread_end_z_mm'] <= p['fillet_start_z_mm']:
        raise ValueError('Thread must end below head fillet')
    if not 0 < p['thread_runout_mm'] < p['thread_end_z_mm']:
        raise ValueError('Invalid thread runout')
    if p['thread_mode'] == 'partial' and not 0 < p['thread_length_reference_mm'] < p['length_mm']:
        raise ValueError('Invalid partial thread length')


def thread_depth(phase, pitch):
    """Radial depth at distance from a crest, with C1 tangent rounded root."""
    q = np.abs((np.asarray(phase)+.5) % 1-.5)
    h = math.sqrt(3)/2*pitch
    radius = h/6
    linear = np.maximum(0, (q-1/16)*pitch*math.sqrt(3))
    rounded = 17*h/24-radius+np.sqrt(np.maximum(0, radius**2-((.5-q)*pitch)**2))
    return np.where(q <= 3/8, linear, rounded)


def _ring_solid(z, radii, segments):
    angles = np.arange(segments)*2*math.pi/segments
    radii = np.broadcast_to(radii, (len(z), segments))
    vertices = np.stack((radii*np.cos(angles), radii*np.sin(angles),
                         np.broadcast_to(np.asarray(z)[:, None], radii.shape)), axis=-1).reshape(-1, 3)
    first = np.arange((len(z)-1)*segments).reshape(-1, segments)
    nxt = np.roll(first, -1, axis=1)
    faces = np.concatenate((np.stack((first, nxt, nxt+segments), axis=-1).reshape(-1, 3),
                            np.stack((first, nxt+segments, first+segments), axis=-1).reshape(-1, 3)))
    bottom, top = len(vertices), len(vertices)+1
    vertices = np.vstack((vertices, [0, 0, z[0]], [0, 0, z[-1]]))
    idx = np.arange(segments)
    caps = np.vstack((np.column_stack((np.full(segments, bottom), (idx+1) % segments, idx)),
                      np.column_stack((np.full(segments, top), idx+(len(z)-1)*segments,
                                       (idx+1) % segments+(len(z)-1)*segments))))
    return trimesh.Trimesh(vertices, np.vstack((faces, caps)), process=True)


def build_model(parameters, variant='full', quality=None):
    """Build a watertight solid mesh from an editable parameter dictionary."""
    if variant not in {'full', 'display'}:
        raise ValueError(f'Unknown detail variant {variant!r}')
    p = resolve_thread(parameters)
    validate_parameters(p)
    quality = quality or {'angular_segments': 96 if variant == 'full' else 32,
                          'samples_per_pitch': 32 if variant == 'full' else 1,
                          'fillet_segments': 12 if variant == 'full' else 4}
    n = quality['angular_segments']
    if n < 12 or n % 4 or quality['samples_per_pitch'] < 1 or quality['fillet_segments'] < 2:
        raise ValueError('Invalid tessellation: angular segments must be a multiple of 4, at least 12')
    if p.get('head_style') == 'headless':
        return build_cup_set_screw(p, variant, quality)
    d, length, pitch = p['diameter_mm'], p['length_mm'], p['pitch_mm']
    rs, rh = d/2, p['head_diameter_mm']/2
    end, tangent = p['thread_end_z_mm'], p['fillet_start_z_mm']
    z = np.linspace(0, end, max(3, math.ceil(end/pitch*quality['samples_per_pitch'])+1))
    z = np.sort(np.r_[z, p['tip_chamfer_mm'], end-p['thread_runout_mm']])
    # A dimension can coincide with a regular pitch sample within floating
    # point rounding. Merge near-equal rings before topology is constructed.
    z = z[np.r_[True, np.diff(z) > 1e-8]]
    theta = np.arange(n)*2*math.pi/n
    r = np.full((len(z), n), rs)
    if variant == 'full':
        # z-theta*P/(2pi) produces a helix rising counterclockwise: right handed.
        phase = z[:, None]/pitch-theta[None, :]/(2*math.pi)
        taper = np.clip((end-z)/p['thread_runout_mm'], 0, 1)
        r -= thread_depth(phase, pitch)*taper[:, None]
    r = np.minimum(r, (rs-p['tip_chamfer_mm']+z)[:, None])
    # Concave fillet tangent to the shaft and the selected head profile.
    style = p.get('head_style', 'countersunk')
    half_angle = math.radians(p['countersink_angle_deg']/2) if style == 'countersunk' else math.pi/2
    a = np.linspace(math.pi, math.pi-half_angle, quality['fillet_segments']+1)
    rf = p['underhead_fillet_mm']
    fillet_z, fillet_r = tangent+rf*np.sin(a), rs+rf+rf*np.cos(a)
    if style == 'countersunk':
        append_z = np.r_[fillet_z, length-p['head_rim_mm'], length]
        append_r = np.r_[fillet_r, rh, rh]
    elif style == 'cylindrical':
        bevel = p['head_edge_chamfer_mm']
        append_z = np.r_[fillet_z, length, length+bevel, p['head_top_z_mm']-bevel, p['head_top_z_mm']]
        append_r = np.r_[fillet_r, rh-bevel, rh, rh, rh-bevel]
    elif style == 'pan':
        sphere = p['head_crown_radius_mm']
        # Published rf is an approximate spherical crown radius. Meet the
        # cylindrical skirt at its exact circular intersection.
        angle = np.linspace(math.asin(rh/sphere), 0, max(16, quality['fillet_segments']*4))
        # Keep the apex cap above trimesh's vertex merge tolerance. The cross
        # cavity removes this tiny cap, including it at high angular resolution.
        arc_r = np.maximum(1e-4, sphere*np.sin(angle))
        arc_z = p['head_top_z_mm']-sphere+sphere*np.cos(angle)
        append_z = np.r_[fillet_z, length, arc_z]
        append_r = np.r_[fillet_r, rh, arc_r]
    else:
        # A spherical segment meeting a flat crown. The nominal shaft radius
        # supplies the crown radius unless a supplier specifies it explicitly.
        crown = p.get('head_crown_diameter_mm', d)/2
        height = p['head_height_mm']-p['head_rim_mm']
        base = length+p['head_rim_mm']
        centre = base+(height*height+crown*crown-rh*rh)/(2*height)
        sphere = math.hypot(rh, base-centre)
        arc_z = np.linspace(length+p['head_rim_mm'], p['head_top_z_mm'],
                            max(12, quality['fillet_segments']*3))
        arc_r = np.sqrt(np.maximum(0, sphere*sphere-(arc_z-centre)**2))
        append_z = np.r_[fillet_z, length, arc_z]
        append_r = np.r_[fillet_r, rh, arc_r]
    # Equal-Z rings with different radii form the annular bearing surface.
    keep = (append_z > z[-1]+1e-9) | ((np.abs(append_z-z[-1]) <= 1e-9) & (np.abs(append_r-r[-1, 0]) > 1e-9))
    z = np.r_[z, append_z[keep]]
    r = np.vstack((r, np.repeat(append_r[keep, None], n, axis=1)))
    body = _ring_solid(z, r, n)
    if p.get('recess_type') in {'H', 'Z'}:
        cutters = cross_recess_cutters(p, n)
    else:
        cutters = hex_recess_cutters(p, n)
    result = trimesh.boolean.difference([body, *cutters], engine='manifold')
    if result is None or not result.is_watertight or result.volume <= 0 or result.body_count != 1:
        raise ValueError('CAD boolean did not produce one watertight solid')
    result.metadata.update(units='mm', variant=variant, parameters=p)
    return result


def build_cup_set_screw(p, variant, quality):
    """Fully threaded headless body, independent socket and concave cup point."""
    length, pitch, d = p['length_mm'], p['pitch_mm'], p['diameter_mm']
    n = quality['angular_segments']
    end_radius = p['thread_minor_diameter_mm']/2
    end_chamfer = d/2-end_radius
    z = np.sort(np.r_[np.linspace(0, length, max(4, math.ceil(length/pitch*quality['samples_per_pitch'])+1)),
                       p['tip_chamfer_mm'], length-end_chamfer])
    z = z[np.r_[True, np.diff(z) > 1e-8]]
    r = np.full((len(z), n), d/2)
    if variant == 'full':
        theta = np.arange(n)*2*math.pi/n
        r -= thread_depth(z[:, None]/pitch-theta[None, :]/(2*math.pi), pitch)
    r = np.minimum(r, (p['cup_diameter_mm']/2+z)[:, None])
    r = np.minimum(r, (end_radius+length-z)[:, None])
    body = _ring_solid(z, r, n)
    inner = p['cup_diameter_mm']/2-p['cup_land_mm']
    depth = inner/math.tan(math.radians(p['cup_angle_deg']/2))
    cup = _ring_solid([-.05, 0, depth], np.array([inner, inner, 1e-6])[:, None], n)
    result = trimesh.boolean.difference([body, cup, *hex_recess_cutters(p, n)], engine='manifold')
    if result is None or not result.is_watertight or result.volume <= 0 or result.body_count != 1:
        raise ValueError('Set screw boolean did not produce one watertight solid')
    result.metadata.update(units='mm', variant=variant, parameters=p)
    return result


def hex_recess_cutters(p, n):
    # Across flats is a socket dimension, distinct from the nominal hex key.
    socket_radius = p['socket_across_flats_mm']/math.sqrt(3)
    cutter = trimesh.creation.cylinder(radius=socket_radius,
        height=p['socket_depth_mm']+.1, sections=6)
    top = p['head_top_z_mm']
    cutter.apply_translation([0, 0, top-p['socket_depth_mm']/2+.05])
    # Permissible countersink at socket mouth, never exceeding the hex corners.
    bevel = socket_radius-p['socket_across_flats_mm']/2
    mouth = _ring_solid([top-bevel, top, top+.05],
        np.asarray([p['socket_across_flats_mm']/2, socket_radius, socket_radius])[:, None], n)
    return [cutter, mouth]


def _rectangle_loft(z0, z1, half_length0, half_length1, half_width0, half_width1):
    """Closed four-sided wing with independent taper on its end and flanks."""
    corners = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]])
    vertices = np.vstack((np.c_[corners*[half_length0, half_width0], np.full(4, z0)],
                          np.c_[corners*[half_length1, half_width1], np.full(4, z1)]))
    faces = [[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7]]
    for i in range(4):
        j = (i+1)%4
        faces += [[i, j, j+4], [i, j+4, i+4]]
    return trimesh.Trimesh(vertices, faces, process=True)


def cross_recess_cutters(p, n):
    """Nominal visual H/Z punch, with tapered wings and a conical floor.

    Published penetration is a gauge dimension. The visual cavity maps it to
    a floor depth; parameters explicitly describe this modelling approximation.
    """
    top, depth = p['head_top_z_mm'], p['recess_depth_mm']
    span = p['recess_diameter_mm']/2
    width = p['recess_wing_width_mm']/2
    core = p['recess_core_width_mm']/2
    floor_height = min(core*math.tan(math.radians(p['recess_floor_angle_deg'])), depth/3)
    z0, z1 = top-depth+floor_height, top+.05
    wing_depth = top-z0
    bottom_span = max(core, span-wing_depth*math.tan(math.radians(p['recess_outer_slope_deg'])))
    top_width = width+wing_depth*math.tan(math.radians(p['recess_wall_taper_deg']))
    # The central conical tip joins the wings without a flat cross-shaped floor.
    centre = _ring_solid([top-depth, z0, z1], np.array([1e-6, core, core+top_width-width])[:, None], n)
    cutters = [centre]
    for angle in (0, math.pi/2):
        wing = _rectangle_loft(z0, z1, bottom_span, span, width, top_width)
        wing.apply_transform(trimesh.transformations.rotation_matrix(angle, [0, 0, 1]))
        cutters.append(wing)
    if p['recess_type'] == 'Z':
        mark_width = p['recess_identification_width_mm']
        # Shallow identification ribs at 45 degrees, distinct from H. Extend
        # below the domed surface at their tips so they remain visible on pan heads.
        mark_depth = min(depth/2, max(mark_width*2, p.get('head_height_mm', 0)/4))
        for angle in (math.pi/4, 3*math.pi/4):
            mark = _rectangle_loft(top-mark_depth, z1, span*.9, span*1.1,
                                   mark_width/3, mark_width/2)
            mark.apply_transform(trimesh.transformations.rotation_matrix(angle, [0, 0, 1]))
            cutters.append(mark)
    return cutters


def apply_gltf_material(tree, material):
    """glTF factors are linear; preserve exact colours rather than 8-bit rounding."""
    colour = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4
              for v in material['base_colour_srgb']]+[1.]
    for entry in tree.get('materials', []):
        entry['pbrMetallicRoughness']['baseColorFactor'] = colour
        if material.get('coat_weight', 0) > 0:
            entry.setdefault('extensions', {})['KHR_materials_clearcoat'] = dict(
                clearcoatFactor=material['coat_weight'],
                clearcoatRoughnessFactor=material['coat_roughness'])
            used = tree.setdefault('extensionsUsed', [])
            if 'KHR_materials_clearcoat' not in used:
                used.append('KHR_materials_clearcoat')


def export_mesh(mesh, filename, p, material=None):
    """STL stays in millimetres; glTF uses metres and Y-up per glTF 2.0."""
    path = Path(filename)
    if path.suffix.lower() == '.glb':
        web = mesh.copy()
        web.apply_transform(np.array([[.001, 0, 0, 0], [0, 0, .001, 0],
                                       [0, -.001, 0, 0], [0, 0, 0, 1]]))
        web.metadata.update(units='metres', source_units='mm', up_axis='Y')
        colour = ([round(c*255) for c in material['base_colour_srgb']]+[255] if material else
                  [52, 56, 60, 255] if p['finish'] == 'black' else [158, 166, 176, 255])
        web.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            name=material['name'] if material else p['finish'], baseColorFactor=colour,
            metallicFactor=material['metallic'] if material else .8,
            roughnessFactor=material['roughness'] if material else .31))
        scene = trimesh.Scene(web)
        scene.metadata.update(units='metres', source_units='mm', up_axis='Y', standard=p.get('standard', 'DIN 7991'))
        path.write_bytes(trimesh.exchange.gltf.export_glb(scene,
            tree_postprocessor=(lambda tree: apply_gltf_material(tree, material)) if material else None))
    else:
        mesh.export(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parameters', type=Path, default=Path(__file__).with_name('parameters.json'))
    parser.add_argument('--length', type=float, help='Change nominal length in mm; recompute thread/shank (under head except countersunk)')
    parser.add_argument('--variant', choices=['full', 'display', 'both'], default='both')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    recipe = json.loads(args.parameters.read_text(encoding='utf-8'))
    params = recipe['parameters']
    if args.length is not None:
        params['length_mm'] = args.length
    args.output.mkdir(parents=True, exist_ok=True)
    for detail in ['full', 'display'] if args.variant == 'both' else [args.variant]:
        mesh = build_model(params, detail, recipe['variants'][detail])
        for suffix in ['stl', 'glb']:
            export_mesh(mesh, args.output/f'model_{detail}.{suffix}', params, recipe.get('material'))
        print(f'{detail}: {len(mesh.faces)} triangles, {mesh.volume:.3f} mm^3')
