"""Persisted studio settings and a headless Blender/Cycles render bridge."""
import copy
from functools import lru_cache
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent


def presentation_defaults(finish='black'):
    black = finish == 'black'
    result = dict(
        material=dict(name='Black oxide steel' if black else 'Satin steel',
            base_colour_srgb=[.205, .218, .235] if black else [.62, .65, .69],
            metallic=.8 if black else 1., roughness=.31 if black else .26,
            roughness_variation=.045, coat_weight=.08 if black else .02,
            coat_roughness=.28, microtexture_spacing_mm=.025,
            microtexture_height_um=.8, note='Visual finish approximation; catalogue specifies colour only.'),
        studio=dict(engine='cycles', device='auto', seed=7991,
            low_samples=48, high_samples=160, adaptive_threshold=.015,
            denoise=True, view_transform='AgX', exposure=0.,
            world_colour=[.78, .82, .9], world_strength=.35,
            floor_colour_srgb=[.93, .935, .94], floor_roughness=.55,
            framing_margin=.13,
            lights=[dict(name='Key softbox', position=[-3, -4, 6],
                         power=650., width=4., height=5., colour=[1., .96, .9]),
                    dict(name='Fill softbox', position=[4, -1, 3],
                         power=330., width=3., height=4., colour=[.9, .95, 1.]),
                    dict(name='Rim strip', position=[1, 4, 4],
                         power=850., width=1.2, height=5., colour=[1., 1., 1.])],
            poses=dict(isometric=dict(camera_eye=[1, -1, 1], projection='orthographic',
                                      orientation='tip down, head up'),
                       product=dict(camera_eye=[-6, -10, 6], projection='orthographic',
                                    orientation='lying on side, head to left', yaw_degrees=-12.,
                                    support='Head rim and threaded shaft rest on ground; solve tilt from mesh.'))),
        renders=dict(low=dict(file='render_low.png', variant='display', pixels=512, view='isometric'),
                     high=dict(file='render_high.png', variant='full', pixels=2048, view='isometric'),
                     product_low=dict(file='render_product_low.png', variant='display', pixels=512, view='product'),
                     product_high=dict(file='render_product_high.png', variant='full', pixels=2048, view='product')))
    material = result['material']
    if finish == 'nylon_white':
        material.update(name='White nylon', base_colour_srgb=[.9, .89, .865], metallic=0.,
                        roughness=.4, coat_weight=0., roughness_variation=.025,
                        microtexture_height_um=.4, note='White nylon visual approximation; resin grade is unspecified.')
    elif finish == 'bright_zinc_plated':
        material.update(name='Bright zinc plated steel', base_colour_srgb=[.73, .76, .8],
                        roughness=.23, roughness_variation=.035,
                        note='Bright zinc finish with neutral cool highlights; passivation colour is unspecified.')
    elif finish == 'net_coat_yellow_plated':
        material.update(name='Net-Coat Yellow-Plated steel',
                        base_colour_srgb=[.79, .64, .32], metallic=1.,
                        roughness=.25, roughness_variation=.035, coat_weight=.12,
                        coat_roughness=.24, microtexture_height_um=.45,
                        note='Screwfix Screw-Tite 2 Net-Coat Yellow-Plated carbon steel, '
                             'zinc and yellow-passivated with wax coating. Warm yellow-gold '
                             'plating visual approximation; not solid brass.')
    elif finish == 'stainless':
        material.update(name='Stainless steel', note='Satin stainless visual approximation; alloy grade is unspecified.')
    elif finish == 'black_zinc':
        material.update(name='Black zinc plated steel', base_colour_srgb=[.13, .14, .155],
                        metallic=.85, roughness=.27, coat_weight=.1,
                        note='Black zinc visual approximation from the supplier product description.')
    elif not finish:
        material['note'] = 'Satin steel visual placeholder because the catalogue does not identify material or finish.'
    return result


def upgrade_presentation(recipe):
    """Add presentation fields without resetting saved geometry or user settings."""
    result = copy.deepcopy(recipe)
    defaults = presentation_defaults(recipe['parameters']['finish'])
    for key in ['material', 'studio']:
        result.setdefault(key, defaults[key])
    for key, render in defaults['renders'].items():
        result.setdefault('renders', {}).setdefault(key, render)
        result['renders'][key].setdefault('view', render['view'])
    return result


@lru_cache(maxsize=1)
def blender_executable():
    configured = os.environ.get('OOMP_BLENDER_EXE')
    if configured:
        path = Path(configured)
        if not path.is_file():
            raise FileNotFoundError(f'OOMP_BLENDER_EXE not found: {configured}')
        return path
    available = shutil.which('blender')
    if available:
        return Path(available)
    candidates = list((Path(os.environ.get('ProgramFiles', 'C:/Program Files'))/
                       'Blender Foundation').glob('Blender */blender.exe'))
    candidates += [Path('/Applications/Blender.app/Contents/MacOS/Blender')]
    existing = sorted((p for p in candidates if p.is_file()), reverse=True)
    if existing:
        return existing[0]
    raise FileNotFoundError('Studio rendering requires Blender 4.5 or newer. Install Blender, '
                            'add it to PATH, or set OOMP_BLENDER_EXE to its executable.')


def renderer_identity():
    path = blender_executable()
    stat = path.stat()
    return dict(executable=str(path), size=stat.st_size, modified_ns=stat.st_mtime_ns)


def render_studio(meshes, p, recipe, output):
    """Transfer mesh geometry with sharp-edge normals; render all poses in one process."""
    import math
    import numpy as np
    import trimesh
    output = Path(output)
    transfer = output/'_render_meshes.npz'
    arrays = {}
    for variant, mesh in meshes.items():
        shaded = trimesh.graph.smooth_shade(mesh, angle=math.pi/5)
        arrays[f'{variant}_vertices'] = shaded.vertices
        arrays[f'{variant}_faces'] = shaded.faces
        arrays[f'{variant}_normals'] = shaded.vertex_normals
    np.savez(transfer, **arrays)
    job = output/'_render_job.json'
    job.write_text(json.dumps(dict(parameters=p, material=recipe['material'],
        studio=recipe['studio'], renders=recipe['renders'], output=str(output.resolve()),
        meshes=str(transfer.resolve())), indent=2), encoding='utf-8')
    command = [str(blender_executable()), '--background', '--factory-startup',
               '--python-exit-code', '1', '--python', str(ROOT/'screw_model_blender.py'),
               '--', str(job.resolve())]
    # Captured output keeps catalogue logs readable; failures retain useful diagnostics.
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        raise RuntimeError(f'Blender studio rendering failed ({result.returncode}):\n'
                           f'{(result.stdout + result.stderr)[-12000:]}')
    missing = [r['file'] for r in recipe['renders'].values() if not (output/r['file']).is_file()]
    if missing or not (output/'studio.blend').is_file() or not (output/'render_scene.json').is_file():
        raise RuntimeError(f'Blender did not produce the complete studio asset set: {missing}')
    transfer.unlink()
    job.unlink()
