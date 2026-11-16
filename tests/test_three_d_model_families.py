"""Family dimensions, distinct drive cavities, migration and standalone output."""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import trimesh
import yaml

import working_three_d_model as models
from screw_model_catalogue import definition
from screw_model_geometry import build_model, resolve_thread
from screw_model_render import presentation_defaults, render_studio, blender_executable


def has_blender():
    try:
        return blender_executable().is_file()
    except FileNotFoundError:
        return False


def recipe(style, d=3, length=12, drive='hex_head', finish='black', **selection):
    part = dict(taxonomy_3=style, taxonomy_4=drive, taxonomy_5=finish,
                taxonomy_6=f"m{str(d).replace('.', '_')}_diameter",
                taxonomy_7=f"{str(length).replace('.', '_')}_mm_length",
                three_d_model_selection=selection)
    models.add_definition(part)
    return part['three_d_model_details']


class FamilyModels(unittest.TestCase):
    def test_socket_cap_dimensions_and_thread_coverage(self):
        for d, dk, k, flats, depth in [(2, 3.8, 2, 1.55, 1), (2.5, 4.5, 2.5, 2.05, 1.1),
                                      (3, 5.5, 3, 2.55, 1.3), (4, 7, 4, 3.05, 2),
                                      (5, 8.5, 5, 4.0575, 2.5), (6, 10, 6, 5.08, 3)]:
            r = recipe('socket_cap', d, 8)
            for variant in ('full', 'display'):
                mesh = build_model(r['parameters'], variant, r['variants'][variant])
                np.testing.assert_allclose(mesh.extents, [dk, dk, 8+k], atol=1e-5)
                section = mesh.section([0, 0, 1], [0, 0, 8+k-depth/2])
                self.assertEqual(len(section.discrete), 2)
                hole = min(section.discrete, key=lambda ring: np.ptp(ring[:, 0]))
                self.assertAlmostEqual(np.ptp(hole[:, 1]), flats, places=5)
        p = resolve_thread(recipe('socket_cap', 5, 120)['parameters'])
        self.assertEqual(p['thread_mode'], 'partial')
        self.assertEqual(p['thread_length_mm'], 22)
        self.assertEqual(resolve_thread(recipe('socket_cap', 5, 120, thread_coverage='full')['parameters'])['thread_mode'], 'full_to_head')
        self.assertEqual(recipe('socket_cap', 4, 4)['length_status'], 'catalogue_length_extension')

    def test_low_head_ultra_uses_confirmed_din_7984_geometry(self):
        for d, height in [(2, 1.3), (2.5, 1.6), (3, 2), (4, 2.8), (5, 3.5), (6, 4)]:
            low, ultra = recipe('socket_cap_low_head', d, 8), recipe('socket_cap_low_head_ultra', d, 8)
            self.assertEqual(low['parameters'], ultra['parameters'])
            self.assertEqual(low['parameters']['head_height_mm'], height)
            self.assertEqual(low['standard'], 'DIN 7984')
            mesh = build_model(low['parameters'], 'full', low['variants']['full'])
            self.assertTrue(mesh.is_watertight)

    def test_button_scope_and_rounded_profile(self):
        for d, dk, k in [(2, 3.5, 1.3), (2.5, 4.5, 1.5), (3, 5.7, 1.65),
                         (4, 7.6, 2.2), (5, 9.5, 2.75), (6, 10.5, 3.3)]:
            r = recipe('button_head', d, 8)
            self.assertEqual(r['dimension_status'], 'manufacturer_extension' if d < 3 else 'standard_dimensions')
            for v in ('full', 'display'):
                mesh = build_model(r['parameters'], v, r['variants'][v])
                np.testing.assert_allclose(mesh.extents, [dk, dk, 8+k], atol=1e-5)
                self.assertEqual(mesh.body_count, 1)

    def test_cross_recesses_are_distinct_and_do_not_break_through(self):
        for style in ('flat_head', 'machine_screw'):
            meshes = []
            for drive in ('philips', 'pozidriv'):
                r = recipe(style, 4, 8, drive)
                mesh = build_model(r['parameters'], 'full', r['variants']['full'])
                self.assertTrue(mesh.is_watertight)
                self.assertEqual(mesh.body_count, 1)
                p = resolve_thread(r['parameters'])
                self.assertGreater(mesh.volume, 0)
                section = mesh.section([0, 0, 1], [0, 0, p['head_top_z_mm']-.4])
                self.assertEqual(len(section.discrete), 2)
                self.assertTrue(any(np.isclose(mesh.vertices[:, 2], p['head_top_z_mm']-p['recess_depth_mm'], atol=1e-5)))
                meshes.append(mesh)
            self.assertNotAlmostEqual(meshes[0].volume, meshes[1].volume, places=3)
        self.assertEqual(recipe('flat_head', 3, 8, 'philips')['parameters']['head_diameter_mm'], 5.6)
        self.assertEqual(recipe('machine_screw', 3, 8, 'pozidriv')['parameters']['head_diameter_mm'], 6)

    def test_cup_grub_socket_depth_depends_on_length(self):
        for d, short_l, long_l, short_t, long_t in [(1.6, 2, 2.5, .7, 1.5),
                (2, 2.5, 3, .8, 1.7), (2.5, 3, 4, 1.2, 2), (3, 4, 5, 1.2, 2),
                (4, 5, 6, 1.5, 2.5), (5, 5, 6, 2, 3), (6, 6, 8, 2, 3.5)]:
            for length, depth in [(short_l, short_t), (long_l, long_t)]:
                r = recipe('grub', d, length)
                self.assertEqual(r['parameters']['socket_depth_mm'], depth)
                for v in ('full', 'display'):
                    m = build_model(r['parameters'], v, r['variants'][v])
                    self.assertTrue(m.is_watertight)
                    self.assertEqual(m.body_count, 1)
                    self.assertAlmostEqual(m.extents[2], length, places=5)
                    # The cup is a separate closed cavity from the opposite hex.
                    sec = m.section([0, 0, 1], [0, 0, .08])
                    self.assertEqual(len(sec.discrete), 2)
                    self.assertEqual(resolve_thread(r['parameters'])['thread_mode'], 'full_to_end')

    def test_specification_requests_and_exclusion_never_generate(self):
        for style, d in [('self_tapping', 2.3), ('wood', 4), ('countersunk', 1.5), ('thread_forming', 2.5)]:
            r = recipe(style, d, 6, 'philips')
            expected = 'excluded' if style == 'thread_forming' else 'needs_specification'
            self.assertEqual(r['generation_status'], expected)
            with tempfile.TemporaryDirectory() as folder:
                models.prepare_files(r, folder)
                out = Path(folder)/'three_d_model'
                self.assertTrue((out/'specification_request.json').is_file())
                self.assertFalse((out/'model.py').exists())
                with self.assertRaisesRegex(ValueError, 'sourced specification'):
                    models.generate_assets(r, folder)

    def test_miniature_supplier_profile_solids_and_cavity(self):
        for length in (3, 4, 5, 6, 8, 10):
            r = recipe('countersunk', 1.4, length, 'philips')
            self.assertEqual(r['generation_status'], 'ready')
            self.assertNotIn('DIN 965', r['standard'])
            self.assertEqual(r['parameters']['pitch_mm'], .3)
            self.assertEqual(r['standard_limits']['cross_penetration_mm'], [.56, .84])
            self.assertIn('not as proof', r['modelling_choices']['recess'])
            for variant in ('full', 'display'):
                mesh = build_model(r['parameters'], variant, r['variants'][variant])
                np.testing.assert_allclose(mesh.extents, [2.5, 2.5, length], atol=1e-5)
                self.assertTrue(mesh.is_watertight)
                self.assertEqual(mesh.body_count, 1)
                self.assertGreater(mesh.volume, 0)
                # Separate mouth and exterior above the bottom of the recess.
                section = mesh.section([0, 0, 1], [0, 0, length-.2])
                self.assertEqual(len(section.discrete), 2)
        # Do not spread the black catalogue reference to a different drive/finish.
        self.assertEqual(recipe('countersunk', 1.4, 3, 'pozidriv')['generation_status'], 'needs_specification')

    def test_partial_wood_evidence_never_becomes_metric_geometry(self):
        proxy = recipe('wood', 4, 50, 'pozidriv', 'bright_zinc_plated')
        self.assertEqual(proxy['generation_status'], 'ready')
        self.assertEqual(proxy['dimension_status'], 'similar_product_visualization')
        self.assertEqual(proxy['parameters']['thread_profile'], 'wood_reference')
        r = proxy['preferred_product_comparison']
        self.assertEqual(r['reference_size_status'], 'size_listed')
        self.assertEqual(r['known_specification']['head_diameter_limits_mm'], [7.6, 8.0])
        self.assertEqual(r['known_specification']['thread_length_limits_mm'], [28.5, 31.5])
        self.assertEqual(r['known_specification']['supplier_sku_as_published'], 'TFST04050')
        self.assertEqual(r['identity_conflicts'][0]['field'], 'finish')
        self.assertNotIn('pitch_mm', r['known_specification'])
        short = recipe('wood', 4, 6, 'pozidriv', 'bright_zinc_plated')['preferred_product_comparison']
        self.assertEqual(short['reference_size_status'], 'length_not_listed')
        self.assertNotIn('thread_length_limits_mm', short['known_specification'])
        small = recipe('wood', 2, 6, 'pozidriv', 'bright_zinc_plated')['preferred_product_comparison']
        self.assertEqual(small['reference_size_status'], 'diameter_not_listed')
        self.assertNotIn('head_diameter_limits_mm', small['known_specification'])
        self.assertIn('source_conflict', recipe('wood', 5, 40, 'pozidriv')['preferred_product_comparison']['known_specification'])
        with tempfile.TemporaryDirectory() as folder:
            models.prepare_files(proxy, folder)
            readme = (Path(folder)/'three_d_model/README.md').read_text()
            self.assertIn('Similar-product', readme)
            self.assertIn('preferred_product_comparison', readme)
            self.assertIn('i-fasteners.com', readme)

    def test_wood_profile_solids_points_and_length_edits(self):
        for d, length, head in [(2, 4, 3.9), (2.5, 5, 4.875), (3, 5, 5.8),
                                (3.5, 8, 6.8), (4, 6, 7.75), (5, 50, 9.75), (6, 120, 11.8)]:
            r = recipe('wood', d, length, 'pozidriv')
            p = resolve_thread(r['parameters'])
            self.assertGreater(p['fillet_start_z_mm']-p['thread_end_z_mm'], 0)
            self.assertEqual(p['thread_mode'], 'partial')
            self.assertNotIn('thread_pitch_diameter_mm', p)
            for variant in ('full', 'display'):
                mesh = build_model(p, variant, r['variants'][variant])
                self.assertTrue(mesh.is_watertight)
                self.assertEqual(mesh.body_count, 1)
                self.assertGreater(mesh.volume, 0)
                np.testing.assert_allclose(mesh.extents, [head, head, length], atol=1e-5)
                tip = mesh.vertices[mesh.vertices[:, 2] < .001]
                self.assertLess(np.linalg.norm(tip[:, :2], axis=1).max(), .001)
                self.assertEqual(len(mesh.section([0, 0, 1], [0, 0, length-.2]).discrete), 2)
        p = recipe('wood', 4, 50, 'pozidriv')['parameters']
        self.assertEqual(resolve_thread(p)['thread_mode'], 'partial')
        p['length_mm'] = 80
        self.assertEqual(resolve_thread(p)['thread_length_mm'], 48)
        p['length_mm'] = 6
        self.assertEqual(resolve_thread(p)['thread_mode'], 'partial')
        # The root and crest must follow independently sourced wood diameters,
        # including an actual section through the full-detail 4 mm helix.
        p = resolve_thread(recipe('wood', 4, 50, 'pozidriv')['parameters'])
        p['length_mm'] = 80
        p = resolve_thread(p)
        mesh = build_model(p, 'full')
        ring = mesh.section([0, 0, 1], [0, 0, 12]).discrete[0]
        radii = np.linalg.norm(ring[:, :2], axis=1)
        self.assertAlmostEqual(radii.min(), 2.375/2, delta=.005)
        self.assertAlmostEqual(radii.max(), 2, delta=.02)
        shank = mesh.section([0, 0, 1], [0, 0, 65]).discrete[0]
        self.assertAlmostEqual(np.linalg.norm(shank[:, :2], axis=1).max(), 2.72/2, places=5)
        self.assertEqual(p['thread_flank_angle_deg'], 40)

    def test_newly_resolved_recipe_removes_stale_request(self):
        with tempfile.TemporaryDirectory() as folder:
            models.prepare_files(recipe('countersunk', 1.5, 3, 'philips'), folder)
            models.prepare_files(recipe('countersunk', 1.4, 3, 'philips'), folder)
            output = Path(folder)/'three_d_model'
            self.assertTrue((output/'parameters.json').is_file())
            self.assertFalse((output/'specification_request.json').exists())
            self.assertFalse((output/'README.md').exists())

    def test_materials_are_suitable_for_nylon_zinc_and_stainless(self):
        nylon = presentation_defaults('nylon_white')['material']
        self.assertEqual(nylon['metallic'], 0)
        self.assertEqual(nylon['name'], 'White nylon')
        self.assertEqual(presentation_defaults('bright_zinc_plated')['material']['name'], 'Bright zinc plated steel')
        self.assertEqual(presentation_defaults('stainless')['material']['metallic'], 1)

    def test_recess_limits_and_commercial_lengths_are_independent(self):
        z = recipe('flat_head', 3, 45, 'pozidriv')
        h = recipe('flat_head', 3, 45, 'philips')
        self.assertEqual(z['standard_limits']['cross_penetration_mm'], [1.48, 1.73])
        self.assertEqual(h['standard_limits']['cross_penetration_mm'], [1.5, 1.8])
        self.assertEqual(z['length_status'], 'catalogue_length_extension')
        self.assertEqual(h['length_status'], 'supplier_length')

    def test_population_preserves_explicit_source_selection(self):
        import working_oomp_populate as populate
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            name = 'hardware_screw_socket_cap_hex_head_black_m5_diameter_120_mm_length'
            path = root/'parts_source'/name/'working.yaml'
            path.parent.mkdir(parents=True)
            path.write_text('three_d_model_selection:\n  thread_coverage: full\n')
            with patch.object(populate, 'Path', lambda value: root/value), patch.object(populate, 'write_extras') as writer:
                populate.main()
            selected = next(v for v in writer.call_args.args[0] if v['taxonomy_3']=='socket_cap' and
                            v['taxonomy_6']=='m5_diameter' and v['taxonomy_7']=='120_mm_length')
            self.assertEqual(selected['three_d_model_selection'], {'thread_coverage': 'full'})
            self.assertEqual(resolve_thread(selected['three_d_model_details']['parameters'])['thread_mode'], 'full_to_head')

    def test_prepare_and_standalone_models_do_not_launch_blender(self):
        r = recipe('socket_cap', 3, 8)
        with tempfile.TemporaryDirectory() as folder, patch('screw_model_render.blender_executable', side_effect=AssertionError('render launched')):
            models.prepare_files(r, folder)
            output = Path(folder)/'three_d_model'
            subprocess.run([sys.executable, str(output/'model.py'), '--length', '20', '--variant', 'display'],
                           check=True, capture_output=True)
            mesh = trimesh.load(output/'model_display.stl')
            self.assertAlmostEqual(mesh.extents[2], 23, places=5)

    def test_ensure_metadata_preserves_ready_recipes_and_rechecks_pending(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            name = 'hardware_screw_socket_cap_hex_head_black_m3_diameter_8_mm_length'
            value = dict(taxonomy_3='socket_cap', taxonomy_4='hex_head', taxonomy_5='black',
                         taxonomy_6='m3_diameter', taxonomy_7='8_mm_length')
            for store in ('parts_source', 'parts'):
                path = root/store/name/'working.yaml'; path.parent.mkdir(parents=True)
                path.write_text(yaml.safe_dump(value))
            with redirect_stdout(io.StringIO()): models.main(root=root, ensure_metadata=True, prepare_only=True)
            path = root/'parts'/name/'working.yaml'
            part = yaml.safe_load(path.read_text()); part['three_d_model_details']['parameters']['length_mm'] = 9
            path.write_text(yaml.safe_dump(part))
            with redirect_stdout(io.StringIO()): models.main(root=root, ensure_metadata=True, check=True)
            self.assertEqual(yaml.safe_load(path.read_text())['three_d_model_details']['parameters']['length_mm'], 9)
            report = json.loads((root/'three_d_model_coverage.json').read_text())
            self.assertEqual(report['counts'], {'ready': 1})

    @unittest.skipUnless(has_blender(), 'Blender required')
    def test_new_heads_launch_both_studio_poses(self):
        # Small temporary smoke renders, never a catalogue render batch.
        for style, drive, finish in [('socket_cap', 'hex_head', 'black'),
                                     ('machine_screw', 'philips', 'nylon_white'),
                                     ('grub', 'hex_head', 'stainless')]:
            r = recipe(style, 3, 8, drive, finish)
            r['studio']['low_samples'] = 4
            for render in r['renders'].values(): render['pixels'] = 48
            p = resolve_thread(r['parameters'])
            meshes = {v: build_model(p, v, r['variants'][v]) for v in ('full', 'display')}
            with tempfile.TemporaryDirectory() as folder:
                render_studio(meshes, p, r, folder)
                scene = json.loads((Path(folder)/'render_scene.json').read_text())
                self.assertEqual(scene['poses']['isometric']['camera_eye'], [1, -1, 1])
                self.assertAlmostEqual(scene['poses']['product']['ground_clearance_mm'], 0, places=5)
                self.assertTrue(all((Path(folder)/r['file']).is_file() for r in r['renders'].values()))


if __name__ == '__main__':
    unittest.main()
