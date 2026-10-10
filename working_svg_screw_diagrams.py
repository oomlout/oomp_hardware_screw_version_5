"""Reusable, length-specific screw artwork in millimetres.

Population owns the drawing recipe. All variants use identical side profiles;
the threaded version adds constant-pitch marks, never stretched artwork.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import opsvg
import svg_styles
import yaml

ROOT = Path(__file__).resolve().parent
NS = 'http://www.w3.org/2000/svg'


SUPPORTED_STYLES = {'countersunk', 'flat_head', 'socket_cap', 'socket_cap_low_head',
                    'socket_cap_low_head_ultra', 'button_head', 'machine_screw',
                    'grub', 'self_tapping', 'thread_forming', 'wood'}


def add_definition(part):
    details = part.get('oobb_details', {})
    style = details.get('screw_style')
    if details.get('oobb_name') != 'screw':
        return False
    if style not in SUPPORTED_STYLES:
        raise ValueError(f'Add a diagram profile for new screw style {style!r}')
    thread, token = details['thread_size'], details['length']
    if not re.fullmatch(r'm[0-9]+(?:_[0-9]+)?_diameter', thread) or not re.fullmatch(r'[0-9]+(?:_[0-9]+)?_mm_length', token):
        raise ValueError(f'Invalid screw diameter/length: {thread}, {token}')
    diameter = float(thread[1:].removesuffix('_diameter').replace('_', '.'))
    length = float(token.removesuffix('_mm_length').replace('_', '.'))
    pitches = {1: .25, 1.2: .25, 1.4: .3, 1.6: .35, 1.7: .35, 2: .4, 2.3: .4,
               2.5: .45, 3: .5, 3.5: .6, 4: .7, 5: .8, 6: 1, 8: 1.25, 10: 1.5, 12: 1.75}
    pitch = pitches.get(diameter, diameter*.18)
    if style in {'wood', 'self_tapping', 'thread_forming'}:
        pitch = diameter*.4
    head_diameter = diameter*(1 if style == 'grub' else 1.7 if style.startswith('socket_cap') else 2)
    part['svg_details'] = dict(svg_name='screw_diagrams', stylesheet='project_bolt',
        screw_style=style, drive_style=details.get('drive_style', 'hex_head'),
        length_mm=length, diameter_mm=diameter, head_diameter_mm=head_diameter,
        head_rim_mm=diameter*.075, socket_width_mm=diameter*.65,
        socket_depth_mm=diameter*.325, thread_pitch_mm=pitch,
        drive_symbol_gap_mm=diameter*.6,
        variants={'threaded': 'diagram_threaded.svg', 'plain': 'diagram_plain.svg',
                  'solid': 'diagram_solid.svg'})
    return True


def profile_dimensions(settings):
    style, diameter = settings['screw_style'], settings['diameter_mm']
    if style in {'countersunk', 'flat_head', 'wood'}:
        head = settings['head_rim_mm']+(settings['head_diameter_mm']-diameter)/2
        return head, settings['length_mm']
    if style == 'grub':
        return 0, settings['length_mm']
    factors = {'socket_cap': 1, 'socket_cap_low_head': .6,
               'socket_cap_low_head_ultra': .3, 'button_head': .5}
    head = diameter*factors.get(style, .6)
    return head, settings['length_mm']+head


def circle_path(x, y, r):
    return f'M{x-r} {y} a{r} {r} 0 1 0 {2*r} 0 a{r} {r} 0 1 0 {-2*r} 0 Z'


def drive_symbol(settings, solid=False):
    """Front-view drive glyph beside the side elevation, in native mm."""
    r = settings['head_diameter_mm']/2
    cx = -settings.get('drive_symbol_gap_mm', settings['diameter_mm']*.6)-r
    size = r*.6
    drive = settings['drive_style']
    if drive == 'hex_head':
        points = [(cx+size*math.cos(i*math.pi/3), size*math.sin(i*math.pi/3)) for i in range(6)]
    elif drive in {'philips', 'phillips', 'pozidriv'}:
        a, b = size, size*.25
        points = [(cx+x, y) for x,y in [(-b,-a),(b,-a),(b,-b),(a,-b),(a,b),(b,b),
                  (b,a),(-b,a),(-b,b),(-a,b),(-a,-b),(-b,-b)]]
    elif drive == 'slotted':
        points = [(cx-size,-size*.22),(cx+size,-size*.22),(cx+size,size*.22),(cx-size,size*.22)]
    else:
        raise ValueError(f'Add a drive glyph for {drive!r}')
    glyph = 'M'+' L'.join(f'{x} {y}' for x,y in points)+' Z'
    if drive == 'pozidriv':
        # Four closed diagonal witness marks distinguish Pozi from Phillips.
        for angle in [math.pi/4+i*math.pi/2 for i in range(4)]:
            ux,uy = math.cos(angle),math.sin(angle)
            glyph += ' M'+' L'.join(f'{cx+ux*d-uy*w} {uy*d+ux*w}' for d,w in
                [(size*.65,-size*.07),(size*1.1,-size*.07),(size*1.1,size*.07),(size*.65,size*.07)])+' Z'
    paths = [] if solid else [('drive-circle','outline.thin',circle_path(cx,0,r))]
    return paths+[('drive-symbol','diagram.solid' if solid else 'outline.thin',glyph)]


def artwork_bounds(settings):
    height = settings['head_diameter_mm']
    gap = settings.get('drive_symbol_gap_mm', settings['diameter_mm']*.6)
    return [-height-gap, -height/2, profile_dimensions(settings)[1], height/2]


def geometry(settings, threaded, solid=False):
    style = settings['screw_style']
    neck, end = profile_dimensions(settings)
    r, hr = settings['diameter_mm']/2, settings['head_diameter_mm']/2
    rim, pitch = settings['head_rim_mm'], settings['thread_pitch_mm']
    chamfer = settings['diameter_mm']*.09
    if end <= neck+chamfer or pitch <= 0:
        raise ValueError('Screw must be longer than its head and tip chamfer')
    if style in {'countersunk', 'flat_head', 'wood'}:
        top, bottom = f'M0 {-hr} H{rim} L{neck} {-r}', f'H{neck} L{rim} {hr} H0 Z'
    elif style == 'grub':
        top, bottom = f'M0 {-r}', 'H0 Z'
    elif style in {'button_head', 'machine_screw', 'self_tapping', 'thread_forming'}:
        top = f'M0 0 Q0 {-hr} {neck} {-hr} V{-r}'
        bottom = f'H{neck} V{hr} Q0 {hr} 0 0 Z'
    else:
        top = f'M0 {-hr+chamfer} L{chamfer} {-hr} H{neck} V{-r}'
        bottom = f'H{neck} V{hr} H{chamfer} L0 {hr-chamfer} Z'
    tip = min(settings['diameter_mm'], (end-neck)/3) if style in {'wood', 'self_tapping', 'thread_forming'} else chamfer
    if tip > chamfer:
        end_path = f'H{end-tip} L{end} 0 L{end-tip} {r}'
    else:
        end_path = f'H{end-chamfer} L{end} {-r+chamfer} V{r-chamfer} L{end-chamfer} {r}'
    outline = top+end_path+bottom
    socket_half = min(settings['socket_width_mm']/2, hr*.6)
    socket = f'M0 {-socket_half} H{settings["socket_depth_mm"]} V{socket_half} H0'
    paths = [('outline', 'diagram.solid' if solid else 'outline.thin', outline)]
    if not solid:
        paths.append(('drive', 'outline.thin', socket))
    if threaded:
        marks = []
        x = neck+pitch
        while x < end-tip-pitch/2:
            marks.append(f'M{x:.5f} {-r+r*.12} L{x-pitch/2:.5f} {r-r*.12}')
            x += pitch
        if marks:
            paths.append(('threads', 'outline.hairline', ' '.join(marks)))
    return paths+drive_symbol(settings, solid)


def render(part, folder):
    settings = part['svg_details']
    styles = svg_styles.get_stylesheet(settings['stylesheet'])
    if settings.get('styles'):
        styles = svg_styles.merge(styles, settings['styles'])
    length, diameter = settings['length_mm'], settings['diameter_mm']
    height = settings['head_diameter_mm']
    _, overall = profile_dimensions(settings)
    bounds = artwork_bounds(settings)
    width = bounds[2]-bounds[0]
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for variant, filename in settings['variants'].items():
        thing = {}
        # Invisible canvas fixes the same margin and physical scale in every variant.
        opsvg.svg_append(thing, shape='rect', size=[width+2, height+2],
                         pos=[(bounds[0]+bounds[2])/2, 0, 0], color='none', stroke='none')
        descriptors = geometry(settings, variant == 'threaded', variant == 'solid')
        for key, style, data in descriptors:
            props = svg_styles.resolve(style, styles)
            opsvg.svg_append(thing, shape='path', d=data, pos=[0, 0, 0], **props)
        path = folder/filename
        opsvg.opsvg_make_object(str(path), thing['svg_components'], padding=0)
        tree = ET.parse(path)
        root = tree.getroot()
        ET.register_namespace('', NS)
        title = ET.Element('{'+NS+'}title')
        title.text = f"{part['id']} / {variant} / 1:1"
        root.insert(0, title)
        metadata = ET.SubElement(root, '{'+NS+'}metadata', {'id': 'oomp-diagram'})
        metadata.text = json.dumps(dict(oomp_id=part['id'], variant=variant, length_mm=length,
            diameter_mm=diameter, head_diameter_mm=height, thread_pitch_mm=settings['thread_pitch_mm'],
            profile_bounds=[0, -height/2, overall, height/2], overall_length_mm=overall, coordinate_units='mm',
            artwork_bounds=bounds, drive_style=settings['drive_style'],
            description='Schematic side elevation; countersunk length includes head, other headed screws measured below head.'))
        group = ET.SubElement(root, '{'+NS+'}g', {'id': 'hardware-diagram'})
        # Keep paths in intrinsic mm coordinates; translate only the root group
        # into its canvas. Consumers can import the child geometry directly.
        group.set('transform', f'translate({1-bounds[0]} {height/2+1})')
        for node, (key, style, _) in zip(list(root.findall('{'+NS+'}path')), descriptors):
            root.remove(node)
            node.attrib.pop('transform', None)
            node.set('data-style', style)
            node.set('data-feature', key)
            node.set('stroke-linecap', 'round')
            node.set('stroke-linejoin', 'round')
            group.append(node)
        tree.write(path, encoding='utf-8', xml_declaration=True)


def main(**kwargs):
    # Synchronize only the requested supported family, preserving all other
    # catalogue metadata and generated image/action records.
    generated = []
    for path in sorted((ROOT/'parts').glob((kwargs.get('filter') or 'hardware_screw_*')+'/working.yaml')):
        part = yaml.safe_load(path.read_text(encoding='utf-8'))
        if kwargs.get('update_metadata', False):
            if not add_definition(part):
                continue
            source_path = ROOT/'parts_source'/part['id']/'working.yaml'
            source = yaml.safe_load(source_path.read_text(encoding='utf-8'))
            source['svg_details'] = copy.deepcopy(part['svg_details'])
            write_recipe(source_path, source['svg_details'])
            write_recipe(path, part['svg_details'])
        if part.get('svg_details', {}).get('svg_name') != 'screw_diagrams':
            continue
        render(part, path.parent)
        generated.append(path.parent)
    return generated


def write_recipe(path, recipe):
    """Update only the generated SVG recipe; retain all other YAML formatting."""
    text = path.read_text(encoding='utf-8')
    block = yaml.safe_dump({'svg_details': recipe}, sort_keys=False)
    pattern = r'^svg_details:.*?(?=^\S|\Z)'
    if re.search(pattern, text, flags=re.MULTILINE | re.DOTALL):
        text = re.sub(pattern, lambda _: block, text, flags=re.MULTILINE | re.DOTALL)
    else:
        text = text.rstrip()+'\n'+block
    path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update-metadata', action='store_true')
    parser.add_argument('--filter', default='hardware_screw_*')
    main(**vars(parser.parse_args()))
