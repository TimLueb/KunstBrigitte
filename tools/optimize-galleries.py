#!/usr/bin/env python3
"""Regenerate gallery previews and HTML using FFmpeg's software decoder."""
import argparse
from contextlib import ExitStack
from pathlib import Path
from html import escape, unescape
import hashlib
import os
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GALLERY = re.compile(r'(<div class="gallery">)(.*?)(</div>)', re.S)
IMAGE = re.compile(r'<img\b[^>]*>')
ATTR = re.compile(r'([\w-]+)="([^"]*)"')
PREVIEW_WIDTHS = (160, 480, 960, 1440)

parser = argparse.ArgumentParser(description='Generate responsive image previews for gallery pages.')
parser.add_argument('pages', nargs='*', metavar='SEITE',
                    help='HTML-Datei(en) im Website-Verzeichnis; ohne Angabe werden alle Seiten verarbeitet')
args = parser.parse_args()
FFMPEG = shutil.which('ffmpeg')
FFPROBE = shutil.which('ffprobe')
if not FFMPEG or not FFPROBE:
    parser.error('FFmpeg und ffprobe müssen installiert und über PATH erreichbar sein.')

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


def run_checked(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        message = result.stderr.decode('utf-8', errors='replace').strip()
        raise RuntimeError(message or f'{command[0]} ist mit Status {result.returncode} fehlgeschlagen.')
    return result


def probe_dimensions(path):
    output = run_checked([
        FFPROBE, '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height', '-of', 'csv=p=0:s=x', str(path)
    ]).stdout.decode('utf-8').strip()
    try:
        width, height = (int(value) for value in output.split('x', 1))
    except (ValueError, TypeError):
        raise RuntimeError(f'Kann Bildmaße nicht lesen: {path}')
    if width < 1 or height < 1:
        raise RuntimeError(f'Ungültige Bildmaße für Vorschau: {path}')
    return width, height


def sample_luminance(paths, directory):
    """Decode small grayscale samples for source/output black-image checks."""
    labels = [f'sample{index}' for index in range(len(paths))]
    filters = [
        f'[{index}:v:0]scale=w=\'min(iw,32)\':h=-2:flags=area,format=gray[{label}]'
        for index, label in enumerate(labels)
    ]
    command = [FFMPEG, '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-xerror']
    for path in paths:
        command.extend(['-hwaccel', 'none', '-autorotate', '-i', str(path)])
    command.extend(['-filter_complex', ';'.join(filters)])
    sample_files = []
    for index, label in enumerate(labels):
        sample = directory / f'check-{index}.raw'
        sample_files.append(sample)
        command.extend(['-map', f'[{label}]', '-frames:v', '1', '-pix_fmt', 'gray',
                        '-f', 'rawvideo', str(sample)])
    run_checked(command)
    means = []
    for path in sample_files:
        pixels = path.read_bytes()
        if not pixels:
            raise RuntimeError(f'Leere Bildprobe: {path}')
        means.append(sum(pixels) / len(pixels))
    return means


def stage_previews(source_path, output_base, temporary_directories, staged_outputs):
    output_base.parent.mkdir(parents=True, exist_ok=True)
    directory = Path(temporary_directories.enter_context(
        tempfile.TemporaryDirectory(prefix='.gallery-preview-stage-', dir=output_base.parent)))
    stage_paths = [directory / f'{output_base.name}-{width}.jpg' for width in PREVIEW_WIDTHS]
    input_labels = [f'input{width}' for width in PREVIEW_WIDTHS]
    output_labels = [f'preview{width}' for width in PREVIEW_WIDTHS]
    split = f'[0:v:0]split={len(PREVIEW_WIDTHS)}' + ''.join(f'[{label}]' for label in input_labels)
    scales = [
        f'[{input_label}]scale=w=\'min(iw,{width})\':h=-2:flags=lanczos,'
        f'format=yuvj420p[{output_label}]'
        for width, input_label, output_label in zip(PREVIEW_WIDTHS, input_labels, output_labels)
    ]
    command = [FFMPEG, '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-xerror',
               '-hwaccel', 'none', '-autorotate', '-i', str(source_path),
               '-filter_complex', ';'.join([split, *scales])]
    for label, path in zip(output_labels, stage_paths):
        command.extend(['-map', f'[{label}]', '-frames:v', '1', '-q:v', '3',
                        '-map_metadata', '-1', str(path)])
    run_checked(command)

    dimensions = []
    for requested_width, path in zip(PREVIEW_WIDTHS, stage_paths):
        if not path.is_file() or path.stat().st_size < 100:
            raise RuntimeError(f'Vorschaudatei fehlt oder ist zu klein: {path}')
        width, height = probe_dimensions(path)
        if width > requested_width:
            raise RuntimeError(f'Vorschau wurde unerwartet vergrößert: {path}')
        dimensions.append((width, height))

    luminance = sample_luminance([source_path, *stage_paths], directory)
    source_mean = luminance[0]
    for path, preview_mean in zip(stage_paths, luminance[1:]):
        if source_mean >= 16 and preview_mean < source_mean * 0.5:
            raise RuntimeError(
                f'Vorschau wirkt deutlich zu dunkel ({preview_mean:.1f} gegenüber '
                f'{source_mean:.1f} Luminanz): {path}')

    previews = []
    seen_widths = set()
    for requested_width, path, (width, height) in zip(PREVIEW_WIDTHS, stage_paths, dimensions):
        if width in seen_widths:
            continue
        seen_widths.add(width)
        target = Path(f'{output_base}-{requested_width}.jpg')
        staged_outputs.append((path, target))
        previews.append({'path': str(target), 'width': width, 'height': height})
    return previews


previews = {}
staged_outputs = []
with ExitStack() as temporary_directories:
    for src in sorted(sources):
        source_path = ROOT / src
        output_base = ROOT / 'Bilder' / 'Vorschauen' / Path(src).relative_to('Bilder')
        previews[str(source_path)] = stage_previews(
            source_path, output_base, temporary_directories, staged_outputs)

    for src, digest in hashes.items():
        if hashlib.sha256((ROOT / src).read_bytes()).hexdigest() != digest:
            raise RuntimeError('Originaldatei wurde während der Umwandlung verändert: ' + src)

    # Staged files are validated and live beside their destinations, so replacement is atomic.
    for staged, target in staged_outputs:
        os.replace(staged, target)

for page, html in pages.items():
    index = [0]
    def image_markup(match):
        attrs = dict(ATTR.findall(match[0]))
        source = unescape(attrs.get('data-original', attrs['src']))
        versions = previews[str((ROOT / source).resolve())]
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
