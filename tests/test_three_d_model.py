"""Independent dimensional, readiness and export checks for screw solids."""
import copy
from contextlib import redirect_stdout
import io
import json
import math
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image
import trimesh
import yaml

import working
import working_oomp_populate as populate
import working_three_d_model as models
from screw_model_geometry import build_model, resolve_thread, thread_depth, export_mesh
from screw_model_views import camera_basis, svg_lines
from screw_model_render import blender_executable, upgrade_presentation


def has_blender():
    try:
        return blender_executable().is_file()
    except FileNotFoundError:
        return False


def part(d=3, length=12):
    value = dict(taxonomy_3='countersunk', taxonomy_4='hex_head', taxonomy_5='black',
                 taxonomy_6=f'm{d}_diameter', taxonomy_7=f'{length}_mm_length')
    models.add_definition(value)
    return value


class ModelTests(unittest.TestCase):
    def test_population_covers_every_target_and_only_target(self):
        with patch.object(populate, 'write_extras') as writer:
            populate.main()
        options = writer.call_args.args[0]
        selected = [p for p in options if p.get('three_d_model_details')]
        self.assertEqual(len(selected), 833)
        from collections import Counter
        self.assertEqual(Counter(p['three_d_model_details'].get('generation_status', 'ready') for p in selected),
                         {'ready': 804, 'needs_specification': 26, 'excluded': 3})
        countersunk = [p for p in selected if p['taxonomy_3'] == 'countersunk'
                       and p['taxonomy_4'] == 'philips']
        self.assertFalse(any(p['taxonomy_6'] == 'm1_5_diameter' for p in countersunk))
        m16 = [p for p in countersunk if p['taxonomy_6'] == 'm1_6_diameter']
        self.assertCountEqual([p['taxonomy_7'] for p in m16],
                              [f'{length}_mm_length' for length in (3, 4, 5, 6, 8, 10)])
        for p in m16:
            self.assertEqual(p['three_d_model_details']['parameters']['diameter_mm'], 1.6)
        for p in options:
            self.assertIn('three_d_model_details', p)
        for p in selected:
            recipe = p['three_d_model_details']
            if recipe.get('generation_status', 'ready') == 'ready':
                self.assertTrue(recipe['sources'])
                from screw_model_geometry import validate_parameters
                validate_parameters(resolve_thread(recipe['parameters']))

    def test_standard_dimensions_and_cavity_survive_mesh_boolean(self):
        for diameter, length, head_diameter, rim, depth, flats in [
                (2, 3, 4, .2, .75, 1.3), (3, 4, 6, .2, 1.075, 2.06),
                (4, 40, 8, .3, 1.675, 2.56)]:
            recipe = part(diameter, length)['three_d_model_details']
            meshes = [build_model(recipe['parameters'], variant, recipe['variants'][variant])
                      for variant in ['full', 'display']]
            for mesh in meshes:
                self.assertTrue(mesh.is_watertight)
                self.assertEqual(mesh.body_count, 1)
                np.testing.assert_allclose(mesh.extents, [head_diameter, head_diameter, length], atol=1e-6)
                wider_than_shaft = np.linalg.norm(mesh.vertices[:, :2], axis=1) > diameter/2+1e-4
                self.assertGreaterEqual(mesh.vertices[wider_than_shaft, 2].min(),
                                        length-recipe['parameters']['head_height_mm']-1e-5)
                # Horizontal section at socket mid-depth has a head outline and a hole.
                section = mesh.section(plane_origin=[0, 0, length-depth/2], plane_normal=[0, 0, 1])
                self.assertEqual(len(section.discrete), 2)
                hole = min(section.discrete, key=lambda poly: np.ptp(poly[:, 0]))
                self.assertAlmostEqual(np.ptp(hole[:, 1]), flats, places=5)
                # The hole closes exactly at the chosen t, and top remains at overall l.
                normals = mesh.face_normals
                bottoms = mesh.triangles_center[(normals[:, 2] > .999) &
                          (np.linalg.norm(mesh.triangles_center[:, :2], axis=1) < flats/2)]
                self.assertTrue(np.any(np.isclose(bottoms[:, 2], length-depth, atol=1e-5)))
            self.assertLess(len(meshes[1].faces), len(meshes[0].faces)/5)
            self.assertLess(meshes[0].volume, meshes[1].volume)

    def test_thread_profile_has_external_rounded_root_and_constant_pitch(self):
        pitch = .5
        self.assertAlmostEqual(float(thread_depth(0, pitch)), 0)
        self.assertAlmostEqual(float(thread_depth(1/16, pitch)), 0)
        self.assertAlmostEqual(float(thread_depth(.5, pitch)), .613434661*pitch, places=8)
        self.assertAlmostEqual(float(thread_depth(3/8, pitch)), .541265877*pitch, places=8)
        samples = np.linspace(-2, 2, 129)
        np.testing.assert_allclose(thread_depth(samples, pitch), thread_depth(samples+1, pitch), atol=1e-12)
        # Two axial sections of the solid a quarter-turn apart have crest heights
        # offset by +P/4, establishing a right-handed rather than mirrored helix.
        p = part()['three_d_model_details']['parameters']
        mesh = build_model(p)
        for x, y, z in [(1.5, 0, 2.0), (0, 1.5, 2.125)]:
            distance = np.min(np.linalg.norm(mesh.vertices-[x, y, z], axis=1))
            self.assertLess(distance, .018)

    def test_partial_thread_and_extension_status(self):
        for d, length, expected in [(3, 20, 'full_to_head'), (3, 25, 'partial'),
                                     (4, 25, 'full_to_head'), (4, 30, 'partial'),
                                     (2, 25, 'full_to_head')]:
            p = part(d, length)['three_d_model_details']['parameters']
            self.assertEqual(p['thread_mode'], expected)
            if expected == 'partial':
                self.assertEqual(p['thread_length_mm'], {3: 12, 4: 14}[d])
                self.assertLessEqual(p['thread_runout_mm'], 2*p['pitch_mm'])
        self.assertEqual(part(2, 3)['three_d_model_details']['dimension_status'], 'manufacturer_extension')
        self.assertEqual(part(3, 4)['three_d_model_details']['length_status'], 'supplier_short_or_extended_length')
        self.assertEqual(part(3, 35)['three_d_model_details']['length_status'], 'supplier_short_or_extended_length')

    def test_glb_uses_metres_and_y_up(self):
        recipe = part()['three_d_model_details']
        p = recipe['parameters']
        mesh = build_model(p, 'display')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'model.glb'
            export_mesh(mesh, path, p, recipe['material'])
            scene = trimesh.load(path, force='scene')
            np.testing.assert_allclose(scene.extents, [.006, .012, .006], atol=1e-8)
            self.assertEqual(scene.metadata['units'], 'metres')
            self.assertEqual(next(iter(scene.geometry.values())).metadata['units'], 'metres')
            material = next(iter(scene.geometry.values())).visual.material
            self.assertAlmostEqual(material.metallicFactor, recipe['material']['metallic'])
            self.assertAlmostEqual(material.roughnessFactor, recipe['material']['roughness'])
            self.assertEqual(material.name, 'Black oxide steel')
            data = path.read_bytes()
            length = struct.unpack_from('<I', data, 12)[0]
            tree = json.loads(data[20:20+length])
            exported = tree['materials'][0]
            expected = [((v+.055)/1.055)**2.4 for v in recipe['material']['base_colour_srgb']]+[1.]
            np.testing.assert_allclose(exported['pbrMetallicRoughness']['baseColorFactor'], expected)
            self.assertIn('KHR_materials_clearcoat', tree['extensionsUsed'])
            self.assertEqual(exported['extensions']['KHR_materials_clearcoat']['clearcoatFactor'], .08)

    def test_svg_isometric_uses_equal_axis_foreshortening_and_hidden_recess(self):
        basis = camera_basis('isometric')
        np.testing.assert_allclose(np.linalg.norm(basis[:, :2], axis=1), math.sqrt(2/3))
        recipe = part()['three_d_model_details']
        mesh = build_model(recipe['parameters'], 'display')
        with tempfile.TemporaryDirectory() as folder:
            for view in ['top', 'bottom']:
                path = Path(folder)/f'{view}.svg'
                svg_lines(mesh, resolve_thread(recipe['parameters']), 'display', view, path, 256)
                root = ET.parse(path).getroot()
                self.assertTrue(root.get('width').endswith('mm'))
                metadata = json.loads(root.find('{http://www.w3.org/2000/svg}metadata').text)
                self.assertEqual(metadata['view'], view)
                # Bottom view must not expose the recessed hex at the other end.
                text = root.find('.//{http://www.w3.org/2000/svg}path').get('d')
                if view == 'bottom':
                    import re
                    xy = np.array([float(x) for x in re.findall(r'-?\d+\.\d+', text)]).reshape(-1, 2)
                    self.assertGreater(np.linalg.norm(xy, axis=1).min(), .9)

    @unittest.skipUnless(has_blender(), 'Blender is required for studio rendering')
    def test_complete_export_cache_and_standalone_regeneration(self):
        recipe = part(2, 3)['three_d_model_details']
        recipe['renders']['low']['pixels'] = 64
        recipe['renders']['high']['pixels'] = 128
        recipe['renders']['product_low']['pixels'] = 64
        recipe['renders']['product_high']['pixels'] = 128
        recipe['studio']['low_samples'] = 12
        with tempfile.TemporaryDirectory() as folder:
            self.assertTrue(models.generate_assets(recipe, folder))
            output = Path(folder)/'three_d_model'
            manifest = json.loads((output/'manifest.json').read_text())
            self.assertEqual(len(manifest['artifacts']), 27)
            self.assertTrue(all(info['watertight'] for info in manifest['models'].values()))
            self.assertEqual(Image.open(output/'render_high.png').size, (128, 128))
            product = np.asarray(Image.open(output/'render_product_high.png'))
            self.assertEqual(product.shape, (128, 128, 3))
            self.assertGreater(float(product.std()), 10.)
            scene = json.loads((output/'render_scene.json').read_text())
            self.assertEqual(scene['engine'], 'Cycles')
            self.assertEqual(scene['poses']['isometric']['camera_eye'], [1, -1, 1])
            support = scene['poses']['product']
            self.assertAlmostEqual(support['ground_clearance_mm'], 0., places=6)
            self.assertAlmostEqual(support['head_contact_mm'], 0., places=5)
            self.assertAlmostEqual(support['shaft_contact_mm'], 0., places=5)
            self.assertGreater((output/'studio.blend').stat().st_size, 1000)
            for variant in ['full', 'display']:
                mesh = trimesh.load(output/f'model_{variant}.stl')
                self.assertTrue(mesh.is_watertight)
                np.testing.assert_allclose(mesh.extents, [4, 4, 3], atol=1e-6)
            self.assertFalse(models.generate_assets(recipe, folder))
            existing = {path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                        for path in output.glob('render*.png')}
            changed_recipe = copy.deepcopy(recipe)
            changed_recipe['studio']['exposure'] = 1.
            with patch.object(models, '_fingerprint', side_effect=AssertionError('No Blender/cache probe expected')):
                self.assertFalse(models.generate_assets(changed_recipe, folder))
            (output/'render_low.png').unlink()
            self.assertTrue(models.generate_assets(recipe, folder))
            for name, snapshot in existing.items():
                if name != 'render_low.png':
                    self.assertEqual(((output/name).read_bytes(), (output/name).stat().st_mtime_ns), snapshot)
            (output/'render_low.png').write_bytes(b'corrupt')
            self.assertFalse(models.generate_assets(recipe, folder))
            self.assertTrue(models.generate_assets(recipe, folder, force=True))
            self.assertEqual(Image.open(output/'render_low.png').size, (64, 64))
            command = [sys.executable, str(output/'model.py'), '--length', '8',
                       '--variant', 'display', '--output', str(output/'custom')]
            subprocess.run(command, cwd=folder, check=True, capture_output=True)
            mesh = trimesh.load(output/'custom/model_display.stl')
            self.assertAlmostEqual(mesh.extents[2], 8, places=5)

    def test_metadata_migration_preserves_unrelated_yaml(self):
        value = part()
        original = 'name: existing\n# Keep this comment\ncustom:\n  nested: unchanged\n'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'working.yaml'; path.write_text(original)
            models.write_recipe(path, value['three_d_model_details'])
            text = path.read_text()
            self.assertTrue(text.startswith(original))
            models.write_recipe(path, value['three_d_model_details'])
            self.assertEqual(path.read_text(), text)
            self.assertEqual(yaml.safe_load(text)['custom'], {'nested': 'unchanged'})

    def test_presentation_upgrade_keeps_custom_geometry_and_settings(self):
        recipe = part()['three_d_model_details']
        recipe['parameters']['length_mm'] = 13.25
        recipe['material']['roughness'] = .42
        del recipe['renders']['product_low']
        del recipe['renders']['product_high']
        recipe['renders']['high']['pixels'] = 800
        upgraded = upgrade_presentation(recipe)
        self.assertEqual(upgraded['parameters'], recipe['parameters'])
        self.assertEqual(upgraded['material'], recipe['material'])
        self.assertEqual(upgraded['renders']['high']['pixels'], 800)
        self.assertEqual(upgraded['renders']['product_high']['view'], 'product')
        self.assertNotIn('product_high', recipe['renders'])

    def test_bad_size_or_impossible_geometry_fails_loudly(self):
        with self.assertRaisesRegex(ValueError, 'sourced dimension row'):
            part(5, 12)
        p = part()['three_d_model_details']['parameters']
        for key, value in [('length_mm', 1), ('pitch_mm', 8),
                           ('socket_across_flats_mm', 20), ('socket_depth_mm', 20)]:
            invalid = copy.deepcopy(p); invalid[key] = value
            with self.assertRaises(ValueError):
                build_model(invalid)


if __name__ == '__main__':
    unittest.main()
