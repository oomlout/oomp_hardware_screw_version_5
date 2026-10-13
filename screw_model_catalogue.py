"""Sourced family selection and explicit specification gaps for every part.

Population uses this lightweight module without importing CAD dependencies.
Recipe parameter dictionaries remain self-contained for standalone generation.
"""
import copy
import fnmatch
from functools import lru_cache
import math
from pathlib import Path
import re

import yaml

from screw_model_render import presentation_defaults

ROOT = Path(__file__).resolve().parent
STANDARDS = ROOT/'source_file/standards'
YAML_LOADER = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
FAMILIES = {
    'socket_cap': dict(priority=1, table='iso_4762.yaml', drive='hex_head'),
    'socket_cap_low_head': dict(priority=2, table='din_7984.yaml', drive='hex_head'),
    'button_head': dict(priority=3, table='iso_7380_1.yaml', drive='hex_head'),
    'grub': dict(priority=4, candidates=['DIN 913 / ISO 4026 flat', 'DIN 914 / ISO 4027 cone',
                                      'DIN 915 / ISO 4028 dog', 'DIN 916 / ISO 4029 cup'],
                 missing=['point_style (flat, cone, dog, cup)', 'sourced headless socket and point dimensions']),
    'countersunk': dict(priority=5, table='din_965.yaml', candidates=['DIN 965', 'ISO 7046-1', 'ISO 7046-2'],
                       missing=['sourced cross recess and head dimensions']),
    'flat_head': dict(priority=6, table='din_965.yaml', candidates=['DIN 965 / ISO 7046'],
                     missing=['sourced head and cross recess dimensions for this miniature size']),
    'machine_screw': dict(priority=7, table='din_7985.yaml', candidates=['DIN 7985 / ISO 7045'],
                         missing=['sourced head and cross recess dimensions for this size']),
    'socket_cap_low_head_ultra': dict(priority=8, candidates=['supplier drawing'],
                                    missing=['supplier head diameter and height', 'socket width and depth', 'thread coverage']),
    'wood': dict(priority=9, candidates=['DIN 7997 if countersunk Pozidriv'],
                 missing=['confirm product identity and length availability', 'head and cross recess dimensions',
                          'thread pitch, core profile, threaded length, taper and point']),
    'self_tapping': dict(priority=10, drive='philips', candidates=['supplier miniature tapping specification'],
                        missing=['actual tapping thread designation and pitch (not inferred from m label)',
                                 'head dimensions, core profile, point form and cross recess dimensions']),
    'thread_forming': dict(priority=11, candidates=['DIN 7500 for metal', 'supplier plastic screw specification'],
                          missing=['metal versus plastic application', 'supplier head and cross recess dimensions',
                                   'thread profile, lobing, lead-in taper and pitch']),
}


@lru_cache(maxsize=None)
def load_standard(name):
    path = (STANDARDS/name).resolve()
    if path.parent != STANDARDS.resolve() or path.suffix != '.yaml':
        raise ValueError('Standard tables must be YAML files directly in source_file/standards')
    value = yaml.load(path.read_text(encoding='utf-8'), Loader=YAML_LOADER)
    if value.get('units') != 'mm' or not value.get('sources'):
        raise ValueError(f'Standard {name} needs millimetre units and source citations')
    return value


def identity(part):
    details = part.get('oobb_details', {})
    style = details.get('screw_style', part.get('taxonomy_3'))
    drive = details.get('drive_style', part.get('taxonomy_4'))
    thread = details.get('thread_size', part.get('taxonomy_6', ''))
    length = details.get('length', part.get('taxonomy_7', ''))
    if not re.fullmatch(r'm\d+(?:_\d+)?_diameter', thread) or not re.fullmatch(r'\d+(?:_\d+)?_mm_length', length):
        raise ValueError(f'Invalid screw diameter or length: {thread}, {length}')
    return style, drive, float(thread[1:].removesuffix('_diameter').replace('_', '.')), float(
        length.removesuffix('_mm_length').replace('_', '.')), details.get('screw_colour', part.get('taxonomy_5', ''))


def definition(part):
    style, drive, diameter, length, finish = identity(part)
    family = FAMILIES.get(style)
    if not family:
        return None
    # Per-part choices survive population when also present in parts_source.
    choices = yaml.load((STANDARDS/'catalogue_selections.yaml').read_text(encoding='utf-8'), Loader=YAML_LOADER)
    selection = copy.deepcopy(choices.get('families', {}).get(style, {}))
    identifier = '_'.join(str(v) for v in ['hardware', 'screw', style, drive, finish,
        part.get('taxonomy_6', part.get('oobb_details', {}).get('thread_size')),
        part.get('taxonomy_7', part.get('oobb_details', {}).get('length'))] if v)
    for match in choices.get('part_filters', []):
        if fnmatch.fnmatchcase(identifier, match['filter']):
            selection.update(match['selection'])
    selection.update(part.get('three_d_model_selection', {}))
    if selection.get('excluded'):
        return dict(schema_version=1, generator='unresolved', generation_status='excluded',
                    family=style, priority=family['priority'], output_folder='three_d_model', units='mm',
                    parameters=dict(diameter_mm=diameter, length_mm=length, finish=finish, drive_style=drive),
                    note=selection.get('identity_note', 'Explicitly excluded from generation.'))
    table = selection.get('standard_file', family.get('table'))
    if table and (drive == family.get('drive', drive)):
        path = STANDARDS/table
        standard = load_standard(table) if path.exists() else None
        row = standard['sizes'].get(f'{diameter:g}') if standard else None
        if row and ('recesses' not in row or drive in row['recesses']):
            return sourced_recipe(style, drive, diameter, length, finish, standard, row, selection)
    missing = family.get('missing', ['sourced dimensional row for this size and drive'])
    recipe = dict(schema_version=1, generator='unresolved', generation_status='needs_specification',
                family=style, priority=family['priority'], output_folder='three_d_model', units='mm',
                parameters=dict(diameter_mm=diameter, length_mm=length, finish=finish, drive_style=drive),
                candidate_standards=family.get('candidates', [table]),
                missing_specification=missing, selection=selection,
                note='No approximate solid is generated. Select a sourced dimension table in three_d_model_selection.')
    if selection.get('research_profile'):
        attach_research(recipe, selection['research_profile'], diameter, length, drive, finish)
    return recipe


def attach_research(recipe, profile, diameter, length, drive, finish):
    """Keep verified partial facts visible without promoting them to CAD inputs."""
    research = load_standard('specification_research.yaml')['profiles'][profile]
    recipe['checked_on'] = research['checked_on']
    recipe['sources'] = copy.deepcopy(research['sources'])
    recipe['known_specification'] = copy.deepcopy(research.get('known_specification', {}))
    recipe['missing_specification'] = list(research['missing_specification'])
    recipe['candidate_standards'] = list(research.get('candidate_standards', []))
    recipe['research_notes'] = list(research.get('notes', []))
    recipe['implementation_requirements'] = list(research.get('implementation_requirements', []))
    size = research.get('sizes', {}).get(f'{diameter:g}')
    if 'sizes' in research:
        recipe['reference_size_status'] = 'diameter_not_listed'
        if size:
            recipe['known_specification'].update(copy.deepcopy(size.get('known_specification', {})))
            products = size.get('products', {})
            recipe['reference_size_status'] = 'length_not_listed'
            recipe['reference_lengths_mm'] = sorted(float(v) for v in products)
            product = products.get(f'{length:g}')
            if product:
                recipe['reference_size_status'] = 'size_listed'
                recipe['known_specification'].update(copy.deepcopy(product))
        if recipe['reference_size_status'] != 'size_listed':
            recipe['missing_specification'].append('Supplier product/drawing for this unlisted diameter/length; do not extrapolate the preferred range.')
    conflicts = []
    for field, actual, expected in [('drive_style', drive, research.get('catalogue_drive')),
                                    ('finish', finish, research.get('catalogue_finish'))]:
        if expected and actual != expected:
            conflicts.append(dict(field=field, catalogue_value=actual, reference_value=expected))
    if conflicts:
        recipe['identity_conflicts'] = conflicts
        recipe['missing_specification'].append('Reconcile the recorded catalogue identity conflicts with the selected supplier product.')
    recipe['note'] = research['note']
    if research.get('use_comparative_supplier_table'):
        table = research['known_specification']['comparative_supplier_table']
        row = table['rows'].get(f'{diameter:g}')
        if row:
            dimensions = {key: value for key, value in zip(table['columns'], row) if value is not None}
            recipe['parameters'].update(dimensions)
            recipe['known_specification'].update(dimensions)
    user_specification = research.get('user_specifications', {}).get(f'{diameter:g}')
    if user_specification and 'pitch_mm' in user_specification:
        recipe['parameters']['pitch_mm'] = user_specification['pitch_mm']
        recipe['known_specification']['pitch_mm'] = user_specification['pitch_mm']
        recipe['known_specification']['pitch_source'] = copy.deepcopy(user_specification)
        recipe['missing_specification'] = [
            'Tapping core diameter and flank/root profile' if 'tapping pitch/lead' in item else item
            for item in recipe['missing_specification']]


def sourced_recipe(style, drive, diameter, length, finish, standard, row, selection):
    p = {key: copy.deepcopy(value) for key, value in row.items() if key not in {
        'dimension_status', 'standard_limits', 'standard_lengths_mm', 'commercial_lengths_mm', 'notes', 'recesses',
                   'socket_depth_long_mm', 'socket_depth_short_mm', 'socket_depth_long_from_length_mm'}}
    if p.get('thread_profile') == 'self_tapping_visualization':
        a = standard['visual_assumptions']
        head, height = p['head_diameter_mm'], p['head_height_mm']
        sag = height*a['crown_sag_height_fraction']
        p.update(thread_minor_diameter_mm=diameter*a['core_diameter_fraction'],
                 point_length_diameters=a['point_length_diameters'],
                 thread_flank_angle_deg=a['thread_flank_angle_deg'],
                 thread_crest_fraction=a['thread_crest_fraction'],
                 thread_runout_pitch_fraction=a['thread_runout_pitch_fraction'],
                 underhead_fillet_mm=diameter*a['underhead_fillet_diameters'],
                 head_crown_radius_mm=((head/2)**2+sag*sag)/(2*sag),
                 head_crown_flat_diameter_mm=head*a['crown_flat_diameter_head_fraction'],
                 recess_type='H', recess_diameter_mm=head*a['recess_diameter_head_fraction'],
                 recess_depth_mm=height*a['recess_depth_height_fraction'],
                 recess_wing_width_mm=head*a['recess_wing_width_head_fraction'],
                 recess_core_width_mm=head*a['recess_core_width_head_fraction'],
                 recess_wall_taper_deg=7., recess_outer_slope_deg=26.5, recess_floor_angle_deg=28.)
    if standard['head_style'] == 'headless':
        p['socket_depth_mm'] = row['socket_depth_long_mm'] if length >= row['socket_depth_long_from_length_mm'] else row['socket_depth_short_mm']
        p['head_diameter_mm'] = diameter  # Envelope for render framing.
        p['head_height_mm'] = 0.
        p['underhead_fillet_mm'] = 0.
    recess = row.get('recesses', {}).get(drive)
    if recess:
        p.update({k: v for k, v in recess.items() if k not in {'penetration_limits_mm', 'commercial_lengths_mm'}})
        drive_table = load_standard('iso_4757.yaml')
        drive_row = drive_table['sizes'][p['recess_type']][str(p['recess_number'])]
        p.update(copy.deepcopy(drive_row))
    p.update(diameter_mm=diameter, length_mm=length, finish=finish, drive_style=drive,
             head_style=standard['head_style'], standard=standard['standard'],
             length_convention=standard['length_convention'],
             tip_chamfer_mm=row['pitch_mm']/2, handedness='right', thread_starts=1,
             thread_coverage=selection.get('thread_coverage', 'standard_reference'))
    if p['head_style'] == 'countersunk':
        p['head_rim_mm'] = row.get('head_rim_mm', p['head_height_mm']-(p['head_diameter_mm']-diameter)/2-p['underhead_fillet_mm']*math.tan(math.pi/8))
    if p['head_style'] == 'headless':
        p['tip_chamfer_mm'] = (diameter-p['cup_diameter_mm'])/2
    if 'thread_length_mm' in selection:
        p['thread_length_reference_mm'] = selection['thread_length_mm']
    # Coordinate metadata and parameters must agree without loading CAD libraries.
    top = length if p['length_convention'] == 'overall' else length+p['head_height_mm']
    pitch = p['pitch_mm']; h = math.sqrt(3)/2*pitch
    p.update(head_top_z_mm=top, overall_length_mm=top)
    if p.get('thread_profile') not in {'wood_reference', 'self_tapping_visualization'}:
        p.update(
             thread_pitch_diameter_mm=diameter-3*h/4,
             thread_minor_diameter_mm=diameter-2*17*h/24,
             thread_root_radius_mm=h/6, thread_flank_angle_deg=60.)
    choices = copy.deepcopy(standard.get('modelling_choices', {}))
    if selection.get('identity_note'):
        choices['identity'] = selection['identity_note']
    choices.update(thread='Nominal right-hand external metric profile; 60 degree flanks, H/6 rounded root; no ISO 965 tolerance offsets.',
                   runout='One-pitch taper; incomplete thread remains within 2P.',
                   tip='Selected 45 degree chamfer of P/2.',
                   display='Smooth nominal thread envelope with the same head and recessed drive.',
                   markings='Unidentified manufacturer and property-class stamps omitted.',
                   certification='Nominal catalogue geometry; not manufacturing certification.',
                   catalogue_length='Unlisted lengths use the sourced size profile at the catalogue length and are explicitly marked as extensions.')
    if p.get('thread_profile') in {'wood_reference', 'self_tapping_visualization'}:
        choices.update(copy.deepcopy(standard['modelling_choices']))
    standard_lengths = row.get('standard_lengths_mm', [])
    commercial_lengths = recess.get('commercial_lengths_mm', []) if recess else row.get('commercial_lengths_mm', [])
    recipe = dict(schema_version=1, generator='parametric_screw', generation_status='ready',
                  family=style, priority=FAMILIES[style]['priority'], output_folder='three_d_model', units='mm',
                  standard=standard['standard'], dimensional_specification=standard['title'],
                  dimension_status=row['dimension_status'], checked_on=standard['checked_on'],
                  length_status='standard_length' if length in standard_lengths else
                                'supplier_length' if length in commercial_lengths else 'catalogue_length_extension',
                  standard_lengths_mm=standard_lengths, commercial_lengths_mm=commercial_lengths,
                  standard_limits=copy.deepcopy(row.get('standard_limits', {})), sources=copy.deepcopy(standard['sources']),
                  parameters=p, modelling_choices=choices,
                  coordinate_system=dict(origin='tip centre', axis='+Z towards head',
                                         length_convention=p['length_convention'], head_top_z_mm=top,
                                         stl_units='mm', glb_units='metres', glb_up_axis='Y'),
                  variants=dict(full=dict(angular_segments=96, samples_per_pitch=32, fillet_segments=12),
                                display=dict(angular_segments=32, samples_per_pitch=1, fillet_segments=4)),
                  views=['isometric', 'front', 'back', 'left', 'right', 'top', 'bottom'],
                  model_formats=['stl', 'glb'])
    if recess:
        recipe['standard_limits']['cross_penetration_mm'] = recess['penetration_limits_mm']
        recipe['sources'] += copy.deepcopy(drive_table['sources'])
        recipe['modelling_choices']['recess'] = standard.get('modelling_choices', {}).get('recess') or ('Published m and midpoint gauge penetration t select a nominal visual cavity. '
            'ISO 4757 wing width and taper guide a four-wing punch with a rounded centre and a conical floor; '
            'Z additionally has four shallow diagonal identification grooves. Die-flow radii and gauge conformity are not certified.')
    recipe.update(presentation_defaults(finish))
    if p.get('thread_profile') == 'self_tapping_visualization':
        recipe['note'] = 'User-authorized image-based self-tapping visualization. Head dimensions and pitch are specified; core, point, crown and recess are documented visual estimates.'
        recipe['selection'] = copy.deepcopy(selection)
        recipe['visual_assumptions'] = copy.deepcopy(standard['visual_assumptions'])
    if p['head_style'] == 'headless':
        recipe['modelling_choices'].update(runout='Thread envelope terminates at the 45 degree cup bevel and socket-end chamfer.',
            tip='Concave 120 degree cup with a small selected annular land and 45 degree outer bevel.',
            socket='Minimum published t for the applicable short/long length category; flat floor is a visualization choice.')
    if p.get('thread_profile') == 'wood_reference':
        recipe['note'] = 'Similar-product modern chipboard/plywood screw visualization; not an exact Screw-Tite model or certified DIN part.'
        recipe['variants']['full'].update(angular_segments=128, samples_per_pitch=64)
        recipe['selection'] = copy.deepcopy(selection)
        comparison = {}
        attach_research(comparison, 'screw_tite', diameter, length, drive, finish)
        recipe['preferred_product_comparison'] = comparison
    return recipe
