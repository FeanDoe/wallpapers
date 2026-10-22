#!/usr/bin/env python3
"""Limpia la metadata de los JPEG: deja solo fecha/hora, zona horaria y orientación.

Elimina GPS, modelo de cámara, MakerNote, XMP, miniaturas, segmentos de
fabricante y datos agregados después del fin de la imagen (p. ej. Samsung).
Conserva el perfil de color ICC. No recomprime la imagen.

Uso: python3 exif.py [carpeta]   (por defecto: wallpapers/)
"""
import struct
import sys
from pathlib import Path

JPEG_EXTS = {".jpg", ".jpeg"}
# Tags que se conservan: IFD0 y Exif IFD.
IFD0_KEEP = {0x0112: "Orientation", 0x0132: "DateTime"}
EXIF_KEEP = {0x9003: "DateTimeOriginal", 0x9010: "OffsetTime", 0x9011: "OffsetTimeOriginal"}


def _segments(d):
    """Itera (marker, bytes_del_segmento) hasta EOI, incluyendo datos de escaneo."""
    if d[:2] != b"\xff\xd8":
        raise ValueError("no es JPEG")
    i = 2
    while i < len(d):
        if d[i] != 0xFF:
            raise ValueError(f"marcador inválido en {i}")
        m = d[i + 1]
        if m == 0xFF:  # relleno
            i += 1
            continue
        if m == 0xD9:  # EOI: lo que venga después se descarta
            yield m, d[i:i + 2]
            return
        if 0xD0 <= m <= 0xD7 or m == 0x01:
            yield m, d[i:i + 2]
            i += 2
            continue
        l = struct.unpack(">H", d[i + 2:i + 4])[0]
        end = i + 2 + l
        if m == 0xDA:  # SOS: avanzar por los datos comprimidos hasta el próximo marcador
            j = end
            while True:
                j = d.index(b"\xff", j)
                n = d[j + 1]
                if n == 0x00 or 0xD0 <= n <= 0xD7 or n == 0xFF:
                    j += 2 if n != 0xFF else 1
                    continue
                break
            end = j
        yield m, d[i:end]
        i = end
    raise ValueError("JPEG sin EOI")


def _read_exif(seg):
    """Devuelve {tag: (type, count, raw_value_bytes)} con los tags a conservar."""
    t = seg[10:]
    e = "<" if t[:2] == b"II" else ">"
    sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1, 9: 4, 10: 8}

    def ifd(o):
        n = struct.unpack(e + "H", t[o:o + 2])[0]
        for k in range(n):
            p = o + 2 + 12 * k
            tag, typ, cnt = struct.unpack(e + "HHI", t[p:p + 8])
            size = sizes.get(typ, 1) * cnt
            if size <= 4:
                raw = t[p + 8:p + 8 + size]
            else:
                off = struct.unpack(e + "I", t[p + 8:p + 12])[0]
                raw = t[off:off + size]
            yield tag, typ, cnt, raw

    kept = {}
    for tag, typ, cnt, raw in ifd(struct.unpack(e + "I", t[4:8])[0]):
        if tag in IFD0_KEEP:
            kept[tag] = (typ, cnt, raw if typ != 3 else struct.pack(">H", struct.unpack(e + "H", raw)[0]))
        elif tag == 0x8769:
            for t2, typ2, cnt2, raw2 in ifd(struct.unpack(e + "I", raw)[0]):
                if t2 in EXIF_KEEP:
                    kept[t2] = (typ2, cnt2, raw2)
    return kept


def _build_exif(kept):
    """Arma un APP1 Exif big-endian mínimo con los tags conservados."""
    ifd0 = sorted(t for t in kept if t in IFD0_KEEP)
    exif = sorted(t for t in kept if t in EXIF_KEEP)
    if not ifd0 and not exif:
        return b""
    n0 = len(ifd0) + (1 if exif else 0)
    ifd0_size = 2 + 12 * n0 + 4
    exif_off = 8 + ifd0_size
    exif_size = 2 + 12 * len(exif) + 4 if exif else 0
    data_off = exif_off + exif_size
    data = b""

    def entries(tags, extra=None):
        nonlocal data
        out = b""
        items = [(t, *kept[t]) for t in tags]
        if extra:
            items.append(extra)
        for tag, typ, cnt, raw in sorted(items):
            if len(raw) <= 4:
                out += struct.pack(">HHI", tag, typ, cnt) + raw.ljust(4, b"\0")
            else:
                out += struct.pack(">HHII", tag, typ, cnt, data_off + len(data))
                data += raw + (b"\0" if len(raw) % 2 else b"")
        return out

    body0 = entries(ifd0, (0x8769, 4, 1, struct.pack(">I", exif_off)) if exif else None)
    body1 = entries(exif) if exif else b""
    tiff = b"MM\x00\x2a" + struct.pack(">I", 8)
    tiff += struct.pack(">H", n0) + body0 + b"\0\0\0\0"
    if exif:
        tiff += struct.pack(">H", len(exif)) + body1 + b"\0\0\0\0"
    tiff += data
    payload = b"Exif\0\0" + tiff
    return b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload


def clean_jpeg(d):
    kept = {}
    out = [b"\xff\xd8"]
    exif_inserted = False
    for m, seg in _segments(d):
        if m == 0xE1 and seg[4:10] == b"Exif\0\0":
            kept.update(_read_exif(seg))
            continue
        if m == 0xFE or (0xE1 <= m <= 0xEF and not (m == 0xE2 and seg[4:16] == b"ICC_PROFILE\0")):
            continue  # comentarios, XMP, MPF, segmentos de fabricante
        if m != 0xE0 and not exif_inserted:
            out.append(None)  # lugar del Exif: después de APP0/JFIF
            exif_inserted = True
        out.append(seg)
    app1 = _build_exif(kept)
    return b"".join(app1 if s is None else s for s in out)


def clean_dir(folder, write=True):
    """Limpia los JPEG de la carpeta. Devuelve la lista de archivos que cambiaron."""
    changed = []
    for p in sorted(Path(folder).iterdir()):
        if p.is_file() and p.suffix.lower() in JPEG_EXTS:
            d = p.read_bytes()
            c = clean_jpeg(d)
            if c != d:
                changed.append(p)
                if write:
                    p.write_bytes(c)
    return changed


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "wallpapers"
    for p in clean_dir(folder):
        print("limpiado:", p.name)
