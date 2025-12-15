import shutil,sys,json
from pathlib import Path
p=Path('fixtures/initial_data.json')
if not p.exists():
    print('FILE NOT FOUND:', p)
    sys.exit(1)
bak = p.with_suffix('.json.bak')
shutil.copy2(p, bak)
raw = p.read_bytes()
encoding='utf-8'
# intento 1: decodificar como utf-8 normal
try:
    text = raw.decode('utf-8')
    # si el texto contiene muchos \x00 indicativos de bytes UTF-16 low/high,
    # reconstruir: encode latin-1 para recuperar bytes y decodificar como utf-16
    if '\x00' in text[:200]:
        try:
            b2 = text.encode('latin-1')
            text = b2.decode('utf-16')
            encoding = 'utf-16 (recovered from utf-8-with-nulls)'
        except Exception:
            # intentar utf-16-le
            try:
                text = b2.decode('utf-16-le')
                encoding = 'utf-16-le (recovered)'
            except Exception:
                pass
except UnicodeDecodeError:
    # intento 2: el archivo puede ser una capa doble (bytes original fueron re-encoded)
    try:
        s = raw.decode('utf-8', errors='strict')
        # recuperar bytes originales (latin-1 roundtrip)
        b2 = s.encode('latin-1')
        # si b2 parece tener BOM de utf-16, decodificar
        if b2.startswith(b'\xff\xfe') or b2.startswith(b'\xfe\xff'):
            text = b2.decode('utf-16')
            encoding = 'utf-16 (roundtrip)'
        else:
            # intentar decodificar b2 como utf-8 o latin-1
            try:
                text = b2.decode('utf-8')
                encoding = 'utf-8 (roundtrip)'
            except Exception:
                text = b2.decode('latin-1')
                encoding = 'latin-1 (roundtrip)'
    except Exception:
        # intento 3: decodificar directamente como utf-16 si tiene BOM
        if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
            try:
                text = raw.decode('utf-16')
                encoding = 'utf-16'
            except Exception as e:
                print('UNABLE TO DECODE as utf-16:', e)
                sys.exit(1)
        else:
            try:
                text = raw.decode('latin-1')
                encoding='latin-1'
            except Exception as e:
                print('UNABLE TO DECODE:', e)
                sys.exit(1)
# debug: mostrar encabezado
print('DETECTED ENCODING:', encoding)
print('HEAD:', repr(text[:200]))
print('HEAD ORD:', [hex(ord(c)) for c in text[:40]])
# write back as utf-8
p.write_text(text, encoding='utf-8')
# validate JSON
try:
    json.loads(text)
    print('CONVERTED OK from', encoding)
except Exception as e:
    print('JSON VALIDATION ERROR:', type(e).__name__, e)
    # Intento de reconstrucción: mapear cada punto de código al byte bajo (ord & 0xFF)
    try:
        b_recon = bytes([ord(c) & 0xFF for c in text])
        try:
            text2 = b_recon.decode('utf-16')
            json.loads(text2)
            p.write_text(text2, encoding='utf-8')
            print('RECONSTRUCTED OK using utf-16 from low-byte mapping')
            sys.exit(0)
        except Exception:
            try:
                text2 = b_recon.decode('utf-8', errors='strict')
                json.loads(text2)
                p.write_text(text2, encoding='utf-8')
                print('RECONSTRUCTED OK using utf-8 from low-byte mapping')
                sys.exit(0)
            except Exception:
                print('RECONSTRUCTION FAILED')
                sys.exit(1)
    except Exception as e2:
        print('RECONSTRUCTION ERROR', e2)
        sys.exit(1)
