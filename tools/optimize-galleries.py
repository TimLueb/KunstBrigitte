#!/usr/bin/env python3
"""Regenerate gallery previews and HTML on macOS.

Run for every page with a gallery, or pass one or more page names, such as
``python3 tools/optimize-galleries.py collagen.html``. Original images remain
untouched. Requires Apple's Swift / ImageIO tools.
"""
import argparse
from pathlib import Path
from html import escape, unescape
import hashlib
import json
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GALLERY = re.compile(r'(<div class="gallery">)(.*?)(</div>)', re.S)
IMAGE = re.compile(r'<img\b[^>]*>')
ATTR = re.compile(r'([\w-]+)="([^"]*)"')

parser = argparse.ArgumentParser(description='Generate responsive image previews for gallery pages.')
parser.add_argument('pages', nargs='*', metavar='SEITE',
                    help='HTML-Datei(en) im Website-Verzeichnis; ohne Angabe werden alle Seiten verarbeitet')
args = parser.parse_args()

if args.pages:
    page_paths = []
    for name in args.pages:
        page = (ROOT / name).resolve()
        if page.parent != ROOT or page.suffix.lower() != '.html' or not page.is_file():
            parser.error(f'Keine HTML-Datei im Website-Verzeichnis: {name}')
        page_paths.append(page)
else:
    page_paths = sorted(ROOT.glob('*.html'))

pages = {}
sources = set()
for page in page_paths:
    html = page.read_text()
    galleries = list(GALLERY.finditer(html))
    if not galleries:
        continue
    pages[page] = html
    for gallery in galleries:
        for tag in IMAGE.findall(gallery[2]):
            attrs = dict(ATTR.findall(tag))
            sources.add(unescape(attrs.get('data-original', attrs['src'])))

if not sources:
    parser.error('In den ausgewählten Seiten wurden keine Galeriebilder gefunden.')

hashes = {src: hashlib.sha256((ROOT / src).read_bytes()).hexdigest() for src in sources}
jobs = [{'source': str(ROOT / src),
         'output': str(ROOT / 'Bilder' / 'Vorschauen' / Path(src).relative_to('Bilder'))}
        for src in sorted(sources)]
with tempfile.TemporaryDirectory(prefix='kunstbrigitte-previews-') as directory:
    manifest = Path(directory) / 'jobs.json'
    manifest.write_text(json.dumps(jobs))
    output = subprocess.check_output(['swift', '-module-cache-path', directory + '/swift-cache',
                                     str(ROOT / 'tools/gallery-previews.swift'), str(manifest)])
previews = json.loads(output)
for src, digest in hashes.items():
    assert hashlib.sha256((ROOT / src).read_bytes()).hexdigest() == digest, 'Original changed: ' + src

for page, html in pages.items():
    index = [0]
    def image_markup(match):
        attrs = dict(ATTR.findall(match[0]))
        source = unescape(attrs.get('data-original', attrs['src']))
        versions = previews[str(ROOT / source)]
        thumbnail = versions[0]
        gallery_versions = versions[1:] or versions
        fallback = gallery_versions[0]
        relative = lambda version: Path(version['path']).relative_to(ROOT).as_posix()
        attrs.update({
            'src': relative(fallback),
            'srcset': ', '.join(f"{relative(v)} {v['width']}w" for v in gallery_versions),
            'sizes': '(max-width: 600px) calc(100vw - 2rem), 260px',
            'width': str(fallback['width']), 'height': str(fallback['height']),
            'loading': 'eager' if index[0] < 2 else 'lazy',
            'decoding': 'async', 'data-original': source,
            'data-thumb': relative(thumbnail),
        })
        index[0] += 1
        # Existing values are HTML-escaped already; decode once before serializing.
        return '<img ' + ' '.join(f'{key}="{escape(unescape(value), quote=True)}"' for key, value in attrs.items()) + '>'
    html = GALLERY.sub(lambda m: m[1] + IMAGE.sub(image_markup, m[2]) + m[3], html)
    page.write_text(html)
    tags = [dict(ATTR.findall(tag))
            for gallery in GALLERY.finditer(html)
            for tag in IMAGE.findall(gallery[2])]
    originals = {unescape(a['data-original']) for a in tags}
    small = {unescape(a['src']) for a in tags}
    old_bytes = sum((ROOT / path).stat().st_size for path in originals)
    new_bytes = sum((ROOT / path).stat().st_size for path in small)
    print(f'{page.name}: {len(tags)} images; originals {old_bytes / 1e6:.2f} MB; small previews {new_bytes / 1e6:.2f} MB')
print(f'Verified {len(hashes)} unchanged originals.')
