"""Regression coverage for the Screwfix identity migration and render material."""
from unittest.mock import patch

import numpy as np

import working_oomp_populate as populate
from oomp_populate_helper import build_oomp_id
from screw_model_catalogue import definition
from screw_model_geometry import build_model
from working_oomp_populate_wood import FINISH, generate


def test_population_emits_only_verified_screwfix_wood_identities():
    with patch.object(populate, 'write_extras') as writer:
        populate.main(filter='hardware_screw_wood_*')
    parts = writer.call_args.args[0]
    assert len(parts) == 30
    assert len({build_oomp_id(part) for part in parts}) == 30
    for part in parts:
        assert part['manufacturer'] == part['taxonomy_14'] == 'screwtite'
        assert part['part_number'] == part['taxonomy_15']
        assert part['taxonomy_5'] == FINISH
        supplier = part['supplier_data']['screwfix']
        assert supplier['supplier_part_number'] == part['part_number']
        assert supplier['supplier_website'].endswith('/'+part['part_number'].lower())
        recipe = part['three_d_model_details']
        assert recipe['generation_status'] == 'ready'
        assert not recipe['preferred_product_comparison'].get('identity_conflicts')
        material = recipe['material']
        assert material['name'] == 'Net-Coat Yellow-Plated steel'
        red, green, blue = material['base_colour_srgb']
        assert red > green > blue
        assert material['metallic'] == 1
    example = next(part for part in parts if part['taxonomy_6'] == 'm4_diameter'
                   and part['taxonomy_7'] == '50_mm_length')
    assert example['part_number'] == '127FY'


def test_new_4_5_mm_size_has_watertight_sourced_geometry():
    part = next(part for part in generate() if part['part_number'] == '731FY')
    recipe = definition(part)
    for variant in ('display', 'full'):
        mesh = build_model(recipe['parameters'], variant, recipe['variants'][variant])
        assert mesh.is_watertight and mesh.body_count == 1 and mesh.volume > 0
        np.testing.assert_allclose(mesh.extents, [8.75, 8.75, 50], atol=1e-5)
