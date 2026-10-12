"""Validated, atomic YAML metadata writes and recovery of generated part files."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile

import yaml

LOADER = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
DUMPER = getattr(yaml, 'CSafeDumper', yaml.SafeDumper)
ROOT = Path(__file__).resolve().parent


def read_yaml(path):
    path = Path(path)
    try:
        value = yaml.load(path.read_text(encoding='utf-8'), Loader=LOADER)
    except (yaml.YAMLError, UnicodeError) as exc:
        mark = getattr(exc, 'problem_mark', None)
        location = f' at line {mark.line+1}, column {mark.column+1}' if mark else ''
        problem = getattr(exc, 'problem', None) or str(exc)
        raise ValueError(f'{path.resolve()}: invalid YAML{location}: {problem}') from exc
    if not isinstance(value, dict):
        raise ValueError(f'{path.resolve()}: expected a YAML metadata mapping')
    return value


def write_text_atomic(path, text, validate_yaml=False):
    """Never open the live file for truncation; publish only a complete payload."""
    path = Path(path)
    if validate_yaml:
        yaml.load(text, Loader=LOADER)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                         dir=path.parent, suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def yaml_text(value, indent=4):
    # Finish serialization before opening any destination. A serializer failure
    # must leave the previous catalogue metadata intact.
    text = yaml.dump(value, Dumper=DUMPER, allow_unicode=True, indent=indent, sort_keys=True)
    yaml.load(text, Loader=LOADER)
    return text


def write_yaml(path, value):
    write_text_atomic(path, yaml_text(value))


def recover_generated(root=ROOT):
    """Explicit maintenance operation: recover invalid working YAML from thing YAML.

    Validate every recovery candidate before writing, verify the companion's part
    ID, and keep the exact original bytes and a recovery report. Source definitions
    and valid generated working files are never replaced.
    """
    root = Path(root).resolve()
    repairs = []
    for path in sorted((root/'parts').glob('*/working.yaml')):
        try:
            read_yaml(path)
        except ValueError as exc:
            companion = path.with_name('thing.yaml')
            if not companion.is_file():
                raise ValueError(f'{path}: cannot recover without a valid thing.yaml') from exc
            value = read_yaml(companion)
            if value.get('id') != path.parent.name:
                raise ValueError(f'{companion}: part ID does not match {path.parent.name}')
            restored = copy.deepcopy(value)
            # These transient controls are omitted by the original working writer.
            restored.pop('make_files', None)
            restored.pop('counter', None)
            repairs.append((path, path.read_bytes(), yaml_text(restored), str(exc)))
    if not repairs:
        print('Generated metadata: all working.yaml files are valid.')
        return dict(repaired=0, backup_directory=None)
    backups = root/'metadata_recovery_backups'
    backups.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    backup = Path(tempfile.mkdtemp(prefix=stamp+'_', dir=backups))
    entries = []
    for path, original, text, error in repairs:
        saved = backup/path.parent.name/'working.yaml'
        saved.parent.mkdir(parents=True)
        saved.write_bytes(original)
        write_text_atomic(path, text)
        entries.append(dict(part=path.parent.name, recovered_from='thing.yaml',
                            original_bytes=len(original), restored_bytes=len(text.encode('utf-8')),
                            original_sha256=hashlib.sha256(original).hexdigest(), error=error))
    report = dict(repaired=len(entries), backup_directory=str(backup), parts=entries)
    write_text_atomic(backup/'report.json', json.dumps(report, indent=2)+'\n')
    print(f'Recovered {len(entries)} generated working.yaml files. Originals saved in {backup}')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repair-generated', action='store_true', required=True,
                        help='Restore invalid generated working.yaml files from matching thing.yaml, retaining backups')
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    recover_generated(args.root)
