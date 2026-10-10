"""Both source variants, every populated style/size, and full-run integration."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from svgpathtools import parse_path
import working
import working_oomp_populate as populate
import working_svg
import working_scad
import working_svg_screw_diagrams as diagrams


class ScrewDiagramTests(unittest.TestCase):
    def test_all_populated_sizes_have_valid_recipes(self):
        with patch.object(populate, 'write_extras') as writer:
            populate.main()
        parts = writer.call_args.args[0]
        self.assertGreater(len(parts), 100)
        for part in parts:
            recipe = part['svg_details']
            for variant in ['threaded', 'plain', 'solid']:
                paths = diagrams.geometry(recipe, variant == 'threaded', variant == 'solid')
                bounds = parse_path(paths[0][2]).bbox()
                self.assertAlmostEqual(bounds[0], 0)
                self.assertAlmostEqual(bounds[1], diagrams.profile_dimensions(recipe)[1])
                features = {key for key, _, _ in paths}
                self.assertEqual('threads' in features, variant == 'threaded')
                self.assertIn('drive-symbol', features)
                self.assertEqual('drive-circle' in features, variant != 'solid')
                if variant == 'solid':
                    self.assertTrue(all(style == 'diagram.solid' for _,style,_ in paths))

    def test_variants_share_exact_outline_and_constant_pitch(self):
        with tempfile.TemporaryDirectory() as folder, redirect_stdout(io.StringIO()):
            counts = []
            for length in [6, 20]:
                part = dict(id=f'test_m2_{length}', oobb_details=dict(oobb_name='screw',
                    screw_style='countersunk', drive_style='hex_head', thread_size='m2_diameter', length=f'{length}_mm_length'))
                diagrams.add_definition(part)
                diagrams.render(part, folder)
                ns = {'s': diagrams.NS}
                variants = {v: ET.parse(Path(folder)/f'diagram_{v}.svg').getroot() for v in ['threaded', 'plain']}
                paths = {v: r.findall(".//s:g[@id='hardware-diagram']/s:path", ns) for v, r in variants.items()}
                self.assertEqual(paths['plain'][0].get('d'), paths['threaded'][0].get('d'))
                self.assertEqual(len(paths['plain']), 4)
                marks = parse_path(paths['threaded'][2].get('d'))
                self.assertAlmostEqual(marks[1].start.real-marks[0].start.real, .4)
                counts.append(len(marks))
            self.assertGreater(counts[1], counts[0])

    def test_full_pipeline_runs_svg_before_scad(self):
        calls = []
        with patch.object(working_svg, 'main', side_effect=lambda **_: calls.append('svg')), \
             patch.object(working_scad, 'main', side_effect=lambda **_: calls.append('scad')):
            working.run(run_oomp_populate=False, run_oomp=False, run_action=False)
        self.assertEqual(calls, ['svg', 'scad'])

    def test_drive_types_and_solid_styles(self):
        part = dict(id='test_drive', oobb_details=dict(oobb_name='screw',
            screw_style='countersunk', drive_style='hex_head', thread_size='m2_diameter', length='10_mm_length'))
        diagrams.add_definition(part)
        glyphs = []
        for drive in ['hex_head', 'philips', 'pozidriv']:
            part['svg_details']['drive_style'] = drive
            paths = diagrams.drive_symbol(part['svg_details'], solid=True)
            self.assertEqual(len(paths), 1)
            self.assertTrue(all(segment.isclosed() for segment in parse_path(paths[0][2]).continuous_subpaths()))
            glyphs.append(paths[0][2])
        self.assertEqual(len(set(glyphs)), 3)
        part['svg_details']['styles'] = {'diagram.solid': {'color': '#123456'}}
        with tempfile.TemporaryDirectory() as folder, redirect_stdout(io.StringIO()):
            diagrams.render(part, folder)
            root = ET.parse(Path(folder)/'diagram_solid.svg').getroot()
            paths = root.findall(".//s:g[@id='hardware-diagram']/s:path", {'s': diagrams.NS})
            self.assertEqual({p.get('data-feature') for p in paths}, {'outline', 'drive-symbol'})
            self.assertTrue(all(p.get('fill') == '#123456' and p.get('stroke') == 'none' for p in paths))


if __name__ == '__main__':
    unittest.main()
