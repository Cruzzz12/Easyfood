#!/usr/bin/env python3
"""
Optimizador simple de imágenes:
- realiza copia de seguridad de archivos originales en media_backup/
- procesa archivos en media/recipes/images y media/recipes/steps
- redimensiona imágenes a ancho máximo 1080 (preserva proporción)
- recomprime jpg/png/webp con valores sensatos
- omite archivos AVIF (los lista en el informe)

ADVERTENCIA: Este script sobrescribe los originales después de hacer backup.
"""
import os
from pathlib import Path
from PIL import Image

BASE = Path(__file__).resolve().parents[1]
MEDIA = BASE / 'media' / 'recipes'
BACKUP = BASE / 'media_backup' / 'recipes'
TARGET_EXTS = ('.jpg', '.jpeg', '.png', '.webp')
MAX_WIDTH = 1080

report = {'processed': [], 'skipped_avif': [], 'errors': []}

def ensure_backup(p: Path):
    dest = BACKUP / p.relative_to(MEDIA)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        p.replace(p) if False else None
        # copiar archivo al backup
        import shutil
        shutil.copy2(p, dest)


def process_image(p: Path):
    try:
        img = Image.open(p)
    except Exception as e:
        report['errors'].append((str(p), str(e)))
        return
    try:
        w, h = img.size
        if w <= MAX_WIDTH and p.suffix.lower() in ('.webp', '.jpg', '.jpeg'):
            # seguir re-guardando para intentar optimizar
            pass
        # calcular redimensión
        if w > MAX_WIDTH:
            new_h = int((MAX_WIDTH / w) * h)
            img = img.resize((MAX_WIDTH, new_h), Image.LANCZOS)
        # save with optimization
        if p.suffix.lower() in ('.jpg', '.jpeg'):
            img = img.convert('RGB')
            img.save(p, format='JPEG', quality=80, optimize=True)
        elif p.suffix.lower() == '.png':
            img.save(p, format='PNG', optimize=True)
        elif p.suffix.lower() == '.webp':
            img.save(p, format='WEBP', quality=80, method=6)
        report['processed'].append(str(p))
    except Exception as e:
        report['errors'].append((str(p), str(e)))


def main():
    if not MEDIA.exists():
        print('No media/recipes folder found, exiting')
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    for sub in ('images', 'steps'):
        d = MEDIA / sub
        if not d.exists():
            continue
        for p in d.rglob('*'):
            if not p.is_file():
                continue
            suffix = p.suffix.lower()
            if suffix == '.avif':
                report['skipped_avif'].append(str(p))
                continue
            if suffix in TARGET_EXTS:
                try:
                    # realizar backup
                    ensure_backup(p)
                except Exception as e:
                    report['errors'].append((str(p), 'backup error: '+str(e)))
                    continue
                process_image(p)
            else:
                # omitir otras extensiones
                report['errors'].append((str(p), 'unsupported ext: '+suffix))
    print('Processed:', len(report['processed']))
    print('Skipped AVIF:', len(report['skipped_avif']))
    if report['errors']:
        print('Errors:', len(report['errors']))
    # escribir informe
    out = BASE / 'image_opt_report.txt'
    with open(out, 'w', encoding='utf-8') as f:
        f.write('Processed files:\n')
        for x in report['processed']:
            f.write(x + '\n')
        f.write('\nSkipped AVIF files:\n')
        for x in report['skipped_avif']:
            f.write(x + '\n')
        f.write('\nErrors:\n')
        for x in report['errors']:
            f.write(str(x) + '\n')
    print('Report saved to', out)

if __name__ == '__main__':
    main()
