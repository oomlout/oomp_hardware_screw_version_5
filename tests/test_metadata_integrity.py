"""Metadata must remain complete if writing fails or generation is interrupted."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

import working_metadata as metadata
import working_oomp


class MetadataIntegrityTests(unittest.TestCase):
    def test_serialization_failure_keeps_previous_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'working.yaml'
            original = b'name: existing\n'
            path.write_bytes(original)
            with self.assertRaises(yaml.representer.RepresenterError):
                metadata.write_yaml(path, {'unsupported': object()})
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(path.parent.glob('*.tmp')), [])

    def test_publish_failure_keeps_previous_file_and_cleans_temporary(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'working.yaml'
            original = b'name: existing\n'
            path.write_bytes(original)
            with patch.object(Path, 'replace', side_effect=OSError('publish failed')):
                with self.assertRaisesRegex(OSError, 'publish failed'):
                    metadata.write_yaml(path, {'name': 'replacement'})
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(path.parent.glob('*.tmp')), [])

    def test_error_names_the_invalid_file_and_line(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'working.yaml'
            path.write_text('name: "unfinished\n')
            with self.assertRaisesRegex(ValueError, 'working.yaml: invalid YAML at line'):
                metadata.read_yaml(path)

    def test_recovery_keeps_original_and_complete_companion_data(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            part = root/'parts'/'example'; part.mkdir(parents=True)
            damaged = b'id: example\nprompt: "unfinished\n'
            (part/'working.yaml').write_bytes(damaged)
            value = dict(id='example', custom={'preserved': True},
                         three_d_model_details={'parameters': {'length_mm': 8}}, make_files=True)
            metadata.write_yaml(part/'thing.yaml', value)
            companion = (part/'thing.yaml').read_bytes()
            report = metadata.recover_generated(root)
            self.assertEqual(report['repaired'], 1)
            saved = Path(report['backup_directory'])/'example'/'working.yaml'
            self.assertEqual(saved.read_bytes(), damaged)
            restored = metadata.read_yaml(part/'working.yaml')
            self.assertEqual(restored['custom'], value['custom'])
            self.assertEqual(restored['three_d_model_details'], value['three_d_model_details'])
            self.assertNotIn('make_files', restored)
            self.assertEqual((part/'thing.yaml').read_bytes(), companion)
            self.assertEqual(metadata.recover_generated(root)['repaired'], 0)

    def test_wrong_companion_identity_prevents_all_repairs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); originals = {}
            for name, companion_id in [('a', 'a'), ('b', 'different')]:
                part = root/'parts'/name; part.mkdir(parents=True)
                path = part/'working.yaml'; path.write_text('name: "unfinished\n')
                originals[path] = path.read_bytes()
                metadata.write_yaml(part/'thing.yaml', {'id': companion_id})
            with self.assertRaisesRegex(ValueError, 'part ID does not match'):
                metadata.recover_generated(root)
            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)

    def test_registration_is_synchronous_and_uses_atomic_writer(self):
        events = []
        def register(**options):
            self.assertFalse(options['make_files'])
            events.append(('register', options['name']))
            return dict(id=options['name'], text='Unicode \u2192 intact', make_files=False)
        def write(path, value):
            events.append(('write', value['id']))
            self.assertEqual(path, Path('parts')/value['id']/'working.yaml')
            self.assertNotIn('make_files', value)
        with patch.object(working_oomp.oomp, 'add_part', side_effect=register), \
             patch.object(working_oomp.oomp, 'add_parts', side_effect=AssertionError('unjoined threads')), \
             patch.object(working_oomp, 'write_yaml', side_effect=write):
            working_oomp.register_parts([{'name': 'a'}, {'name': 'b'}])
        self.assertEqual(events, [('register', 'a'), ('write', 'a'), ('register', 'b'), ('write', 'b')])

    def test_registration_respects_no_file_mode(self):
        with patch.object(working_oomp.oomp, 'add_part', return_value={'id': 'a'}), \
             patch.object(working_oomp, 'write_yaml') as writer:
            working_oomp.register_parts([{'name': 'a'}], make_files=False)
        writer.assert_not_called()

    def test_real_oomp_registration_publishes_complete_unicode_metadata(self):
        value = dict(taxonomy_1='hardware', taxonomy_2='screw', taxonomy_3='socket_cap',
                     taxonomy_4='hex_head', taxonomy_5='black', taxonomy_6='m3_diameter',
                     taxonomy_7='8_mm_length', note='Unicode \u2192 intact '+('quoted "text" '*5000))
        with tempfile.TemporaryDirectory() as folder, patch.dict(working_oomp.oomp.parts, clear=True):
            working_oomp.register_parts([value], make_files=folder)
            path = Path(folder)/'hardware_screw_socket_cap_hex_head_black_m3_diameter_8_mm_length'/'working.yaml'
            saved = metadata.read_yaml(path)
            self.assertEqual(saved['note'], value['note'])
            self.assertEqual(saved['taxonomy_6'], value['taxonomy_6'])
            self.assertGreater(path.stat().st_size, 65536)


if __name__ == '__main__':
    unittest.main()
