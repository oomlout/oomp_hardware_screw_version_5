"""The supplied envelopes survive approximation, booleans and length edits."""
import unittest

import numpy as np

from screw_model_catalogue import definition
from screw_model_geometry import build_model, resolve_thread
from working_oomp_populate_self_tapping import generate


class SelfTappingModels(unittest.TestCase):
    def test_all_catalogue_solids_and_full_thread_coverage(self):
        options = generate()
        self.assertEqual(len(options), 26)
        self.assertFalse(any(p['taxonomy_6'] == 'm2_3_diameter' for p in options))
        for option in options:
            with self.subTest(size=option['taxonomy_6'], length=option['taxonomy_7']):
                recipe = definition(option)
                self.assertEqual(recipe['generation_status'], 'ready')
                self.assertEqual(recipe['dimension_status'], 'image_based_visualization')
                p = resolve_thread(recipe['parameters'])
                self.assertEqual(p['thread_mode'], 'full_to_head')
                self.assertEqual(p['shank_length_min_mm'], 0)
                self.assertAlmostEqual(p['thread_end_z_mm'], p['length_mm']-p['underhead_fillet_mm'])
                if p['diameter_mm'] in (1, 1.2):
                    self.assertEqual(p['pitch_mm'], .3)
                volumes = []
                for variant in ('full', 'display'):
                    mesh = build_model(recipe['parameters'], variant, recipe['variants'][variant])
                    self.assertTrue(mesh.is_watertight)
                    self.assertEqual(mesh.body_count, 1)
                    self.assertGreater(mesh.volume, 0)
                    np.testing.assert_allclose(mesh.extents,
                        [p['head_diameter_mm']]*2+[p['length_mm']+p['head_height_mm']], atol=2e-5)
                    # Outside and cavity loops through the cross, with a solid floor below it.
                    section = mesh.section([0, 0, 1], [0, 0, p['head_top_z_mm']-.35*p['head_height_mm']])
                    self.assertEqual(len(section.discrete), 2)
                    floor = mesh.section([0, 0, 1], [0, 0, p['head_top_z_mm']-p['recess_depth_mm']-.02])
                    self.assertEqual(len(floor.discrete), 1)
                    # The point is tapered; threads remain present close to the head.
                    tip = mesh.section([0, 0, 1], [0, 0, .1*p['point_length_mm']])
                    self.assertLess(np.ptp(tip.vertices[:, 0]), .15*p['diameter_mm'])
                    if variant == 'full':
                        shaft = mesh.section([0, 0, 1], [0, 0, p['thread_end_z_mm']-.5*p['pitch_mm']])
                        radii = np.linalg.norm(shaft.vertices[:, :2], axis=1)
                        self.assertGreater(np.ptp(radii), .12*p['diameter_mm'])
                    volumes.append(mesh.volume)
                self.assertLess(volumes[0], volumes[1])
                edited = resolve_thread(dict(recipe['parameters'], length_mm=30))
                self.assertEqual(edited['thread_mode'], 'full_to_head')
                self.assertAlmostEqual(edited['thread_end_z_mm'], 30-edited['underhead_fillet_mm'])
