"""Offline OOMP README generation. Depends only on PyYAML; never builds assets."""
from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
import re
from urllib.parse import quote

import yaml

START = '<!-- oomp-documentation:start -->'
END = '<!-- oomp-documentation:end -->'
IMAGES = ('three_d_model/render_product_low.png', 'three_d_model/render_low.png',
          '3dpr_presentation.png', '3dpr.png', 'image.png', 'image.jpg',
          'data/working_svg_square_pins_300.png', 'data/working_svg_top_300.png',
          'images/pcb_3d_populated.png', 'initial_generated.png')


def text(value):
    return html.escape(str(value)).replace('|', '&#124;').replace('\n', ' ').replace('[', '&#91;').replace(']', '&#93;').replace('`', '&#96;')


def link(target, page):
    return quote(os.path.relpath(target, page.parent).replace('\\', '/'), safe='/.-_')


def write(path, content):
    if path.is_symlink():
        raise ValueError(f'Refusing linked output: {path}')
    content = content.rstrip() + '\n'
    if path.exists() and path.read_text(encoding='utf-8') == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8', newline='\n')


def managed(path, body):
    old = path.read_text(encoding='utf-8') if path.exists() else ''
    block = START + '\n' + body.rstrip() + '\n' + END
    if START in old or END in old:
        if old.count(START) != 1 or old.count(END) != 1 or old.index(START) > old.index(END):
            raise ValueError(f'Malformed documentation markers: {path}')
        write(path, old[:old.index(START)] + block + old[old.index(END) + len(END):])
    else:
        # Keep specialist material at its original relative-link location.
        retained = '\n\n<details>\n<summary>Existing technical notes</summary>\n\n' + old.rstrip() + '\n\n</details>' if old.strip() else ''
        write(path, block + retained)


def preview(folder):
    return next((folder / name for name in IMAGES if (folder / name).is_file()), None)


def part_body(data, folder, root):
    page = folder / 'README.md'
    title = data.get('name_proper') or data.get('name') or folder.name.replace('_', ' ')
    lines = [f'# {text(title)}', '', '## Summary', '',
             f'OOMP catalogue record for {text(title)}. Use the metadata to identify this variant and the part folder to inspect its available assets.', '']
    picture = preview(folder)
    if picture:
        lines += [f'![Catalogue preview of {text(title)}]({link(picture, page)})', '',
                  'Catalogue illustration; consult the source dimensions and datasheet for specification.', '']
    lines += ['## Details', '', f'**OOMP folder ID:** `{folder.name}`', '',
              f'[Catalogue](../../README.md) · [Part metadata](working.yaml)', '',
              '| Field | Value |', '| --- | --- |']
    for key in ('id', 'short_code', 'short_code_alpha', 'md5_6', 'md5_6_alpha', 'oomp_key', *[f'taxonomy_{i}' for i in range(1, 16)]):
        if data.get(key) not in (None, ''):
            lines.append(f'| {text(key)} | {text(data[key])} |')
    metadata = yaml.dump(data, Dumper=getattr(yaml, 'CSafeDumper', yaml.SafeDumper), sort_keys=False, allow_unicode=True)
    fence = '`' * max(3, max((len(m[0])+1 for m in re.finditer(r'`+', metadata)), default=3))
    lines += ['', '<details>', '<summary>Full part metadata</summary>', '', fence+'yaml', metadata.rstrip(), fence, '', '</details>', '',
              '## Parts', '', '[Open the canonical part folder](./) for the files available for this variant. Alternative model formats describe the same record; they are not extra components.', '',
              '## Assembly', '', 'No assembly procedure is inferred from this catalogue record. Use any retained technical notes and the original manufacturer documentation for installation details.']
    return '\n'.join(lines)


def generate(root):
    root = Path(root).resolve()
    config = json.loads((root / 'documentation.json').read_text(encoding='utf-8'))
    records = []
    loader = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
    for source in sorted((root / 'parts').glob('*/working.yaml')):
        if source.is_symlink() or source.parent.is_symlink():
            raise ValueError(f'Linked part source: {source}')
        data = yaml.load(source.read_text(encoding='utf-8'), Loader=loader)
        if not isinstance(data, dict):
            raise ValueError(f'Expected part mapping: {source}')
        if data.get('taxonomy_1') == 'navigation':
            continue
        records.append((source.parent, data))
    page = root / 'README.md'
    lines = [f'# {config["title"]}', '', '## Summary', '', config['summary'], '']
    example = next(((folder, picture, data) for folder, data in records if (picture := preview(folder))), None)
    picture = example[1] if example else None
    if picture:
        folder, picture, data = example
        title = text(data.get('name_proper') or folder.name.replace('_', ' '))
        lines += [f'[![Catalogue illustration of {title}]({link(picture, page)})]({link(folder, page)}/)', '',
                  f'Representative example: {title}. Other variants differ.', '']
    lines += ['## Details', '', f'[OOMP version 5 directory](https://github.com/oomlout/oomlout_oomp_version_5) · [Generator and maintenance guide](README_GENERATOR.md)', '']
    if config.get('source_repository'):
        lines += [f'[Full source catalogue]({config["source_repository"]})', '']
    lines += ['## Parts', '']
    if records:
        lines += [f'Browse **{len(records)} records** in the [part folders](parts/).', '']
    else:
        target = config.get('browse')
        lines += [f'[Browse the catalogue]({target})' if target else 'No generated part records are present in this checkout yet.', '']
    lines += ['## Assembly', '', config.get('assembly', 'Choose an exact record before using its files. Installation and compatibility depend on the selected component; refer to its technical notes.'), '']
    # Root content is deliberately small; earlier setup stays in README_GENERATOR.
    write(page, START + '\n' + '\n'.join(lines).rstrip() + '\n' + END)
    if config.get('part_pages', True):
        for folder, data in records:
            managed(folder / 'README.md', part_body(data, folder, root))
    return {'repository': root.name, 'parts': len(records), 'part_pages': config.get('part_pages', True), 'preview': bool(picture)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(generate(args.project)))
