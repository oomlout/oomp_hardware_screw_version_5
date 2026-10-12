"""Populate and generate sourced screw solids and presentation assets."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import copy
import fnmatch
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

import yaml

from screw_model_render import presentation_defaults, upgrade_presentation
from working_metadata import read_yaml, write_text_atomic

ROOT = Path(__file__).resolve().parent
STANDARD_FILE = ROOT/'source_file/standards/din_7991.yaml'
GENERATOR_NAME = 'din_7991_countersunk'
SCHEMA_VERSION = 1
_STANDARD = None
YAML_LOADER = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)


def _standard():
    global _STANDARD
    if _STANDARD is None:
        _STANDARD = yaml.load(STANDARD_FILE.read_text(encoding='utf-8'), Loader=YAML_LOADER)
    return _STANDARD


def add_definition(part):
    """Attach sourced geometry or a specification request for every screw family."""
    details = part.get('oobb_details', {})
    style = details.get('screw_style', part.get('taxonomy_3'))
    drive = details.get('drive_style', part.get('taxonomy_4'))
    if style != 'countersunk' or drive != 'hex_head':
        from screw_model_catalogue import definition
        recipe = definition(part)
        if recipe is None:
            return False
        part['three_d_model_details'] = recipe
        return True
    thread = details.get('thread_size', part.get('taxonomy_6', ''))
    length_token = details.get('length', part.get('taxonomy_7', ''))
    if not re.fullmatch(r'm\d+(?:_\d+)?_diameter', thread) or not re.fullmatch(r'\d+(?:_\d+)?_mm_length', length_token):
        raise ValueError(f'Invalid diameter or length: {thread}, {length_token}')
    diameter = float(thread[1:].removesuffix('_diameter').replace('_', '.'))
    length = float(length_token.removesuffix('_mm_length').replace('_', '.'))
    standard = _standard()
    try:
        size = standard['sizes'][f'{diameter:g}']
    except KeyError as exc:
        raise ValueError(f'DIN 7991 M{diameter:g} needs a sourced dimension row') from exc
    parameters = {key: copy.deepcopy(value) for key, value in size.items()
                  if key not in {'dimension_status', 'standard_limits', 'standard_lengths_mm', 'commercial_lengths_mm', 'notes'}}
    parameters.update(diameter_mm=diameter, length_mm=length, countersink_angle_deg=90.,
        tip_chamfer_mm=size['pitch_mm']/2, handedness='right', thread_starts=1,
        finish=details.get('screw_colour', part.get('taxonomy_5', 'black')))
    # Keep population lightweight: derived coordinates use only stdlib math.
    import math
    parameters['head_rim_reference_mm'] = size['head_rim_mm']
    # DIN c is approximate. Adjust the flat rim to accommodate the tangent
    # fillet while keeping dk at nominal and the complete head within k max.
    parameters['head_rim_mm'] = (size['head_height_mm']-(size['head_diameter_mm']-diameter)/2-
                               size['underhead_fillet_mm']*math.tan(math.pi/8))
    h = math.sqrt(3)/2*size['pitch_mm']
    parameters.update(thread_pitch_diameter_mm=diameter-3*h/4,
        thread_minor_diameter_mm=diameter-2*17*h/24,
        thread_root_radius_mm=h/6, thread_flank_angle_deg=60.)
    tangent = length-size['head_height_mm']
    partial = size['partial_thread_from_length_mm'] is not None and length >= size['partial_thread_from_length_mm']
    end = min(size['thread_length_reference_mm']+size['pitch_mm'], tangent) if partial else tangent
    parameters.update(fillet_start_z_mm=tangent, thread_end_z_mm=end,
        thread_runout_mm=min(size['pitch_mm'], end/3),
        thread_mode='partial' if partial else 'full_to_head')
    parameters['thread_length_mm'] = end-parameters['thread_runout_mm']
    parameters['grip_length_mm'] = length-parameters['thread_length_mm']
    parameters['shank_length_min_mm'] = max(0, parameters['grip_length_mm']-5*size['pitch_mm']) if partial else 0
    if end <= 0 or length <= size['socket_depth_mm']:
        raise ValueError('Length is too short for this DIN 7991 head')
    part['three_d_model_details'] = dict(schema_version=SCHEMA_VERSION,
        generator=GENERATOR_NAME, output_folder='three_d_model', units='mm',
        standard=standard['standard'], dimension_status=size['dimension_status'],
        dimensional_specification=('Supplier DIN 7991-style M2 (Bossard BN 20 / Newstar)' if diameter == 2
                                  else standard['standard']),
        length_status=('manufacturer_extension' if diameter == 2 else
                       'standard_length' if length in size['standard_lengths_mm'] else
                       'supplier_short_or_extended_length' if length in size['commercial_lengths_mm'] else 'nonstandard_catalogue_length'),
        sources=copy.deepcopy(standard['sources']), checked_on=standard['checked_on'],
        standard_limits=copy.deepcopy(size['standard_limits']),
        standard_lengths_mm=copy.deepcopy(size['standard_lengths_mm']),
        parameters=parameters,
        modelling_choices=dict(dimension_selection='Nominal/max head and shaft, midpoint socket limits for M3/M4.',
            head_rim='Approximate DIN c reference reduced by r*tan(22.5 degrees) so the fillet fits within k max.',
            thread='ISO metric nominal external profile; rounded root R=H/6; no ISO 965 tolerance offsets.',
            runout='One pitch taper to nominal shaft diameter; maximum incomplete thread is 2P.',
            tip='45 degree tip chamfer of P/2; selected end form under DIN 78.',
            socket='Flat bottom hex socket with permissible circular mouth countersink within hex corners.',
            display='Smooth nominal-diameter thread envelope; lower tessellation, same head/recess/end dimensions.',
            markings='Manufacturer identity and property-class stamps omitted: catalogue does not identify them.',
            certification='Standards-based nominal catalogue geometry, not a tolerance-gauged manufacturing certification.',
            size_note=size.get('notes', 'DIN 7991:1986 dimensional row.')),
        coordinate_system=dict(origin='tip centre', axis='+Z towards head', head_top_z_mm=length,
                               stl_units='mm', glb_units='metres', glb_up_axis='Y'),
        variants=dict(full=dict(angular_segments=96, samples_per_pitch=32, fillet_segments=12),
                      display=dict(angular_segments=32, samples_per_pitch=1, fillet_segments=4)),
        renders=dict(low=dict(file='render_low.png', variant='display', pixels=512),
                     high=dict(file='render_high.png', variant='full', pixels=2048)),
        views=['isometric', 'front', 'back', 'left', 'right', 'top', 'bottom'],
        model_formats=['stl', 'glb'])
    part['three_d_model_details'].update(presentation_defaults(parameters['finish']))
    return True


def write_recipe(path, recipe):
    """Replace just the top-level recipe, preserving all existing YAML blocks."""
    path = Path(path)
    original = path.read_text(encoding='utf-8')
    block = yaml.safe_dump({'three_d_model_details': recipe}, sort_keys=False, allow_unicode=True)
    pattern = r'^three_d_model_details:.*?(?=^\S|\Z)'
    text = re.sub(pattern, lambda _: block, original, flags=re.MULTILINE | re.DOTALL) if re.search(
        pattern, original, flags=re.MULTILINE | re.DOTALL) else original.rstrip()+'\n'+block
    if text != original:
        write_text_atomic(path, text, validate_yaml=True)


def prepare_files(recipe, folder):
    """Install portable inputs, or a concrete request for missing specifications."""
    output = Path(folder)/'three_d_model'
    output.mkdir(parents=True, exist_ok=True)
    if recipe.get('generation_status', 'ready') != 'ready':
        (output/'specification_request.json').write_text(json.dumps(recipe, indent=2)+'\n', encoding='utf-8')
        text = 'This catalogue entry is '+recipe['generation_status']+'.\n\n'+recipe.get('note', '')+'\n'
        if recipe.get('known_specification'):
            text += '\nVerified reference information (not model inputs):\n\n'+ '\n'.join(
                f'- {key}: {value}' for key, value in recipe['known_specification'].items())+'\n'
        if recipe.get('reference_size_status'):
            text += '\nReference size status: '+recipe['reference_size_status']+'\n'
        if recipe.get('identity_conflicts'):
            text += '\nCatalogue conflicts:\n\n'+ '\n'.join(
                f"- {v['field']}: catalogue {v['catalogue_value']}; reference {v['reference_value']}"
                for v in recipe['identity_conflicts'])+'\n'
        if recipe.get('missing_specification'):
            text += '\nStill required:\n\n'+'\n'.join('- '+v for v in recipe['missing_specification'])+'\n'
        if recipe.get('implementation_requirements'):
            text += '\nGeometry implementation required:\n\n'+'\n'.join(
                '- '+v for v in recipe['implementation_requirements'])+'\n'
        if recipe.get('sources'):
            text += '\nSources:\n\n'+'\n'.join(
                f"- [{v['title']}]({v['url']})" for v in recipe['sources'])+'\n'
        (output/'README.md').write_text(text, encoding='utf-8')
        return
    recipe = upgrade_presentation(recipe)
    (output/'parameters.json').write_text(json.dumps(recipe, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    shutil.copyfile(ROOT/'screw_model_geometry.py', output/'model.py')
    shutil.copyfile(ROOT/'requirements-three-d-model.txt', output/'requirements.txt')
    stale_request = output/'specification_request.json'
    if stale_request.is_file():
        stale_request.unlink()
    stale_readme = output/'README.md'
    if stale_readme.is_file() and stale_readme.read_text(encoding='utf-8').startswith('This catalogue entry is '):
        stale_readme.unlink()
    write_visualization_note(recipe, output)


def write_visualization_note(recipe, output):
    if recipe.get('dimension_status') != 'similar_product_visualization':
        return
    text = recipe['note']+'\n\nDimensions and assumptions:\n\n'
    text += '\n'.join(f'- {key}: {value}' for key, value in recipe['modelling_choices'].items())
    text += '\n\nSources:\n\n'+'\n'.join(f"- [{v['title']}]({v['url']})" for v in recipe['sources'])
    text += '\n\nThe preferred Screw-Tite product evidence and unresolved brand differences are preserved in parameters.json under preferred_product_comparison.\n'
    (output/'README.md').write_text(text, encoding='utf-8')


def coverage_report(root, pattern='*', check=False):
    """Persist catalogue readiness and validate inputs without starting Blender."""
    from collections import Counter
    rows, errors = [], []
    for path in sorted((root/'parts').glob('*/working.yaml')):
        if not fnmatch.fnmatchcase(path.parent.name, pattern):
            continue
        part = read_yaml(path)
        recipe = part.get('three_d_model_details')
        if not recipe:
            rows.append(dict(part=path.parent.name, family=part.get('taxonomy_3'), status='missing_recipe', priority=99))
            continue
        status = recipe.get('generation_status', 'ready')
        row = dict(part=path.parent.name, family=recipe.get('family', 'countersunk'), status=status,
                   priority=recipe.get('priority', 5), standard=recipe.get('standard'),
                   dimension_status=recipe.get('dimension_status'), length_status=recipe.get('length_status'),
                   missing_specification=recipe.get('missing_specification', []))
        for key in ('reference_size_status', 'reference_lengths_mm', 'identity_conflicts', 'implementation_requirements'):
            if key in recipe:
                row[key] = copy.deepcopy(recipe[key])
        if check and status == 'ready':
            from screw_model_geometry import resolve_thread, validate_parameters
            try:
                validate_parameters(resolve_thread(recipe['parameters']))
                row['parameter_check'] = 'passed'
            except (ValueError, KeyError, TypeError) as exc:
                row['parameter_check'] = 'failed'
                row['error'] = str(exc)
                errors.append(row)
        rows.append(row)
    rows.sort(key=lambda r: (r['priority'], r['family'], r['part']))
    counts = dict(Counter(row['status'] for row in rows))
    report = dict(schema_version=1, filter=pattern, total=len(rows), counts=counts,
                  validation='parameters_checked' if check else 'not_requested', errors=errors, parts=rows)
    output = root/'three_d_model_coverage.json'
    output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(f'3D coverage: {counts}; {len(errors)} invalid recipes. Report: {output}', flush=True)
    if errors:
        raise ValueError('\n'.join(f"{row['part']}: {row['error']}" for row in errors))
    return report


def _fingerprint(recipe):
    digest = hashlib.sha256(json.dumps(recipe, sort_keys=True).encode())
    for name in ['working_three_d_model.py', 'screw_model_catalogue.py', 'screw_model_geometry.py', 'screw_model_views.py',
                 'screw_model_render.py', 'screw_model_blender.py', 'requirements-three-d-model.txt']:
        digest.update((ROOT/name).read_bytes())
    from screw_model_render import renderer_identity
    digest.update(json.dumps(renderer_identity(), sort_keys=True).encode())
    from importlib.metadata import version
    for dependency in ['numpy', 'trimesh', 'manifold3d', 'Pillow', 'numba']:
        digest.update(f'{dependency}={version(dependency)}'.encode())
    return digest.hexdigest()


def assets_exist(recipe, folder):
    """Reuse complete output sets regardless of recipe, code or dependency changes."""
    output = Path(folder)/'three_d_model'
    expected = {'manifest.json', 'model.py', 'parameters.json', 'requirements.txt', 'studio.blend', 'render_scene.json'}
    expected.update(f'model_{variant}.{suffix}' for variant in recipe['variants'] for suffix in recipe['model_formats'])
    expected.update(f'{variant}/{view}.svg' for variant in recipe['variants'] for view in recipe['views'])
    expected.update(render['file'] for render in recipe['renders'].values())
    return all((output/name).is_file() for name in expected)


def generate_assets(recipe, folder, force=False):
    """Fill missing outputs, preserving existing renders unless force is requested."""
    recipe = upgrade_presentation(recipe)
    if recipe.get('generation_status', 'ready') != 'ready':
        raise ValueError('This part needs a sourced specification before generating a solid')
    if recipe.get('schema_version') != SCHEMA_VERSION or recipe.get('generator') not in {GENERATOR_NAME, 'parametric_screw'}:
        raise ValueError('Unsupported model recipe schema or generator')
    if recipe.get('output_folder') != 'three_d_model' or recipe.get('model_formats') != ['stl', 'glb']:
        raise ValueError('Unsupported output folder or model formats')
    if set(recipe['variants']) != {'full', 'display'}:
        raise ValueError('Both full and display variants are required')
    if not force and assets_exist(recipe, folder):
        return False
    from screw_model_geometry import build_model, export_mesh, resolve_thread
    from screw_model_views import export_views, VIEWS
    from screw_model_render import render_studio
    if recipe['views'] != list(VIEWS):
        raise ValueError('Unsupported view set')
    output = Path(folder)/'three_d_model'
    output.mkdir(parents=True, exist_ok=True)
    fingerprint = _fingerprint(recipe)
    manifest_path = output/'manifest.json'
    with tempfile.TemporaryDirectory(prefix='.build-', dir=output) as directory:
        stage = Path(directory)
        write_visualization_note(recipe, stage)
        (stage/'parameters.json').write_text(json.dumps(recipe, indent=2, sort_keys=True)+'\n', encoding='utf-8')
        shutil.copyfile(ROOT/'screw_model_geometry.py', stage/'model.py')
        shutil.copyfile(ROOT/'requirements-three-d-model.txt', stage/'requirements.txt')
        measurements = {}
        meshes = {}
        p = resolve_thread(recipe['parameters'])
        for variant, quality in recipe['variants'].items():
            mesh = build_model(p, variant, quality)
            meshes[variant] = mesh
            measurements[variant] = dict(triangles=len(mesh.faces), vertices=len(mesh.vertices),
                watertight=bool(mesh.is_watertight), connected_solids=mesh.body_count,
                volume_mm3=float(mesh.volume), bounds_mm=mesh.bounds.tolist())
            for suffix in recipe['model_formats']:
                export_mesh(mesh, stage/f'model_{variant}.{suffix}', p, recipe['material'])
            export_views(mesh, p, variant, stage)
        studio_files = [render['file'] for render in recipe['renders'].values()]
        reused_renders = set()
        if not force:
            for name in studio_files:
                if (output/name).is_file():
                    shutil.copy2(output/name, stage/name)
                    reused_renders.add(name)
            if len(reused_renders) == len(studio_files) and all(
                    (output/name).is_file() for name in ['studio.blend', 'render_scene.json']):
                for name in ['studio.blend', 'render_scene.json']:
                    shutil.copy2(output/name, stage/name)
        studio_files += ['studio.blend', 'render_scene.json']
        if not all((stage/name).is_file() for name in studio_files):
            # The Blender worker skips PNGs copied from the existing output.
            render_studio(meshes, p, recipe, stage)
        artifacts = {str(path.relative_to(stage)).replace('\\', '/'): dict(bytes=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in sorted(stage.rglob('*')) if path.is_file()}
        manifest = dict(schema_version=SCHEMA_VERSION, fingerprint=fingerprint, standard=recipe['standard'],
            dimension_status=recipe['dimension_status'], length_status=recipe['length_status'],
            models=measurements, artifacts=artifacts)
        # Publish manifest last: an interrupted build never passes a cache check.
        for name in artifacts:
            if name in reused_renders:
                continue
            destination = output/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            (stage/name).replace(destination)
        temp_manifest = stage/'manifest.json'
        temp_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n', encoding='utf-8')
        temp_manifest.replace(manifest_path)
    return True


def main(**kwargs):
    root = Path(kwargs.get('root', ROOT))
    pattern = kwargs.get('filter') or '*'
    update = kwargs.get('update_metadata', False)
    ensure = kwargs.get('ensure_metadata', False)
    update_presentation = kwargs.get('update_presentation', False)
    count = dict(updated=0, prepared=0, generated=0, cached=0, needs_specification=0, excluded=0)
    jobs = kwargs.get('model_jobs', 1)
    if not isinstance(jobs, int) or not 1 <= jobs <= 8:
        raise ValueError('model_jobs must be an integer between 1 and 8')
    # Migrate both stores independently; preserve hand-edited/action metadata.
    if update or ensure or update_presentation:
        for store in ['parts_source', 'parts']:
            for path in sorted((root/store).glob('*/working.yaml')):
                if not fnmatch.fnmatchcase(path.parent.name, pattern):
                    continue
                part = read_yaml(path)
                old = part.get('three_d_model_details')
                refresh = update or (ensure and (not old or old.get('generation_status', 'ready') != 'ready'))
                if refresh and add_definition(part):
                    write_recipe(path, part['three_d_model_details'])
                    if old != part['three_d_model_details']:
                        count['updated'] += 1
                elif update_presentation and part.get('three_d_model_details') and part['three_d_model_details'].get('generation_status', 'ready') == 'ready':
                    recipe = upgrade_presentation(part['three_d_model_details'])
                    if recipe != part['three_d_model_details']:
                        write_recipe(path, recipe)
                        count['updated'] += 1
    tasks = []
    if kwargs.get('check', False) or kwargs.get('report_only', False):
        coverage_report(root, pattern, check=kwargs.get('check', False))
        return count
    for path in sorted((root/'parts').glob('*/working.yaml')):
        if not fnmatch.fnmatchcase(path.parent.name, pattern):
            continue
        part = read_yaml(path)
        recipe = part.get('three_d_model_details')
        if not recipe:
            raise ValueError(f'{path}: missing model recipe; run with --ensure-metadata')
        if recipe.get('generation_status', 'ready') != 'ready':
            count['excluded' if recipe['generation_status'] == 'excluded' else 'needs_specification'] += 1
            if not kwargs.get('metadata_only', False):
                prepare_files(recipe, path.parent)
                count['prepared'] += 1
            continue
        if kwargs.get('metadata_only', False):
            continue
        if kwargs.get('prepare_only', False):
            prepare_files(recipe, path.parent)
            count['prepared'] += 1
            continue
        tasks.append((recipe, path.parent, kwargs.get('force', False)))
    # Priority keeps socket caps first even when a whole catalogue is requested.
    tasks.sort(key=lambda task: (task[0].get('priority', 5), task[1].name))
    if not kwargs.get('metadata_only', False):
        coverage_report(root, pattern, check=True)
    if any(force or not assets_exist(upgrade_presentation(recipe), folder) for recipe, folder, force in tasks):
        from screw_model_render import blender_executable
        blender_executable()  # Fail before mesh work if rendering cannot launch.
    if jobs == 1:
        for task in tasks:
            name, changed = _generate_one(task)
            count['generated' if changed else 'cached'] += 1
            print(f'  3D {"generated" if changed else "cached"}: {name}', flush=True)
    elif tasks:
        # Each worker owns a different part directory and publishes atomically.
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            futures = [pool.submit(_generate_one, task) for task in tasks]
            for future in as_completed(futures):
                name, changed = future.result()
                count['generated' if changed else 'cached'] += 1
                print(f'  3D {"generated" if changed else "cached"}: {name}', flush=True)
    print(f'3D models: {count}', flush=True)
    return count


def _generate_one(task):
    recipe, folder, force = task
    return folder.name, generate_assets(recipe, folder, force)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--filter', default='*')
    parser.add_argument('--update-metadata', action='store_true')
    parser.add_argument('--ensure-metadata', action='store_true', help='Add missing recipes and recheck specification requests; preserve existing ready recipes')
    parser.add_argument('--update-presentation', action='store_true',
                        help='Add studio materials and product views, preserving saved geometry and custom settings')
    parser.add_argument('--metadata-only', action='store_true')
    parser.add_argument('--prepare-only', action='store_true', help='Write standalone inputs and specification requests without building meshes or rendering')
    parser.add_argument('--check', action='store_true', help='Check every selected ready recipe and write a coverage report, without renders')
    parser.add_argument('--report-only', action='store_true', help='Write readiness report without CAD imports or renders')
    parser.add_argument('--force', action='store_true', help='Rebuild all outputs, including existing renders')
    parser.add_argument('--jobs', dest='model_jobs', type=int, default=1,
                        help='Independent model worker processes, 1–8 (default 1)')
    try:
        main(**vars(parser.parse_args()))
    except ValueError as exc:
        parser.exit(1, f'3D model error: {exc}\n')
