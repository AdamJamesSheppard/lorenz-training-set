#!/usr/bin/env python3
"""Check the compiled monograph and render every page for visual inspection."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf'
PDF = OUT / 'lorenz_solver_monograph.pdf'
QA = ROOT / 'tmp/pdfs/solver_monograph_qa'


def main():
    QA.mkdir(parents=True, exist_ok=True)
    info = subprocess.check_output(['pdfinfo', str(PDF)], text=True)
    pages = int(re.search(r'Pages:\s+(\d+)', info).group(1))
    text = subprocess.check_output(['pdftotext', str(PDF), '-'], text=True)
    log = (OUT / 'lorenz_solver_monograph.log').read_text()
    errors = [line for line in log.splitlines() if any(token in line for token in
              ('undefined', 'Overfull', 'Missing character', 'Fatal error'))]
    if errors:
        raise RuntimeError('\n'.join(errors))
    for required in ('Bibliography', 'Complete recorded Git chronology',
                     'Source ledger and evidence index', 'Crank', 'SIPG'):
        if required not in text:
            raise RuntimeError(f'Missing expected content: {required}')
    if '??' in text:
        raise RuntimeError('Unresolved printed cross-reference')
    bbox = subprocess.check_output(['pdftotext', '-bbox', str(PDF), '-'], text=True)
    # Poppler maps a few legacy TeX math delimiters to XML-invalid controls.
    # Remove those text glyph mappings only; the word coordinates stay intact.
    control_pattern = r'[\x00-\x08\x0b\x0c\x0e-\x1f]'
    mapped_controls = len(re.findall(control_pattern, bbox))
    bbox = re.sub(control_pattern, '', bbox)
    tree = ET.fromstring(bbox)
    outside = []
    for number, page in enumerate(tree.iter('{http://www.w3.org/1999/xhtml}page'), 1):
        width, height = float(page.attrib['width']), float(page.attrib['height'])
        for word in page.iter('{http://www.w3.org/1999/xhtml}word'):
            if (float(word.attrib['xMin']) < 0 or float(word.attrib['yMin']) < 0
                or float(word.attrib['xMax']) > width
                or float(word.attrib['yMax']) > height):
                outside.append({'page': number, 'text': word.text})
    if outside:
        raise RuntimeError(f'Text outside page bounds: {outside}')
    subprocess.run(['pdftoppm', '-scale-to', '700', '-png', str(PDF),
                    str(QA / 'page')], check=True)
    images = sorted(QA.glob('page-*.png'))
    sheets = []
    for start in range(0, len(images), 16):
        sheet = Image.new('RGB', (1120, 1640), 'white')
        draw = ImageDraw.Draw(sheet)
        for offset, path in enumerate(images[start:start + 16]):
            im = Image.open(path).convert('RGB')
            im.thumbnail((270, 380))
            x, y = (offset % 4) * 280, (offset // 4) * 410
            sheet.paste(im, (x, y + 22))
            draw.text((x + 8, y + 5), f'PDF page {start + offset + 1}', fill='black')
        path = QA / f'contact-{start // 16 + 1:02}.png'
        sheet.save(path)
        sheets.append(str(path.relative_to(ROOT)))
    report = {'pdf': str(PDF.relative_to(ROOT)), 'sha256': hashlib.sha256(PDF.read_bytes()).hexdigest(),
              'pages': pages, 'word_count_approximate': len(text.split()),
              'latex_error_checks': 'PASS', 'text_bounds_check': 'PASS',
              'poppler_xml_control_glyph_mappings_removed': mapped_controls,
              'all_pages_rendered': len(images), 'contact_sheets': sheets,
              'visual_review': 'pending human-agent inspection'}
    (OUT / 'solver_monograph_qa.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
