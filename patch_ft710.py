#!/usr/bin/env python3
"""
Apply the JDM -> DEV patch to the FT-710_MAIN_V0112.SFL (18 bytes) file. 

Usage: python3 patch_ft710.py path/to/FT-710_MAIN_V0112.SFL 

- DO NOT modify the original: write the result in./patched/FT-710_MAIN_V0112. SFL 
- Before touching anything, check that each original byte matches the expected. 
  If something doesn't match (another firmware version, file corrupt), abort without writing anything. 
  
- Offsets and values exit the FT-710_MARS_MOD.md document diff (Nikolay-Kha/ft710-internals). 
Compare them yourself with that diff.

*********************************************************************************************************
*********************************************************************************************************

Aplica el parche JDM -> DEV al archivo FT-710_MAIN_V0112.SFL (18 bytes).

Uso:
    python3 patch_ft710.py ruta/al/FT-710_MAIN_V0112.SFL

- NO modifica el original: escribe el resultado en ./patched/FT-710_MAIN_V0112.SFL
- Antes de tocar nada verifica que cada byte original coincida con lo
  esperado. Si algo no coincide (otra version de firmware, archivo
  corrupto), aborta sin escribir nada.
- Los offsets y valores salen del diff del documento FT-710_MARS_MOD.md
  (Nikolay-Kha/ft710-internals). Comparalos tu mismo con ese diff.
"""
import hashlib
import pathlib
import sys

# (offset, byte original, byte nuevo)
PATCH = [
    # Cabecera: checksum maestro "B092FD93" -> "3FE2DEAD" (ASCII)
    (0x220, 0x42, 0x33),
    (0x221, 0x30, 0x46),
    (0x222, 0x39, 0x45),
    # 0x223 no cambia (0x32)
    (0x224, 0x46, 0x44),
    (0x225, 0x44, 0x45),
    (0x226, 0x39, 0x41),
    (0x227, 0x33, 0x44),
    # Codigo parcheado (cifrado en el .SFL)
    (0x9B518, 0x62, 0x4E),
    (0x9B51A, 0x56, 0x64),
    (0x9B51B, 0x70, 0x63),
    (0x9B51C, 0x61, 0x6E),
    (0x9B51D, 0x3E, 0x4B),
    (0x9B52C, 0x4F, 0x4C),
    (0x9B52D, 0x48, 0x55),
    (0x9B532, 0x59, 0x5A),
    (0x9B533, 0x66, 0x5C),
    (0x9B534, 0x6E, 0x59),
    (0x9B54D, 0x5A, 0x57),
]

EXPECTED_NAME = "FT-710_MAIN_V0112.SFL"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    src = pathlib.Path(sys.argv[1])
    if src.name != EXPECTED_NAME:
        print(f"AVISO: el archivo se llama {src.name}, se esperaba {EXPECTED_NAME}.")

    data = bytearray(src.read_bytes())
    print(f"Archivo: {src}  ({len(data)} bytes)")
    print(f"SHA-256 original: {sha256(bytes(data))}")

    if len(data) <= max(off for off, _, _ in PATCH):
        print("ERROR: el archivo es demasiado corto, no es el firmware esperado.")
        return 1

    already = [data[o] == new for o, _, new in PATCH]
    if all(already):
        print("Este archivo YA tiene el parche aplicado. No se hace nada.")
        return 0

    bad = [(o, data[o], old) for o, old, _ in PATCH if data[o] != old]
    if bad:
        print("ERROR: los bytes no coinciden con el firmware esperado. No se escribe nada.")
        for o, found, old in bad:
            print(f"  offset 0x{o:X}: encontrado {found:02X}, esperado {old:02X}")
        print("Probablemente no es la version 202402 / MAIN V0112 original.")
        return 1

    for o, _, new in PATCH:
        data[o] = new

    out_dir = pathlib.Path("patched")
    out_dir.mkdir(exist_ok=True)
    dst = out_dir / EXPECTED_NAME
    dst.write_bytes(bytes(data))

    # Verificacion: releer y contar diferencias contra el original
    orig = src.read_bytes()
    new = dst.read_bytes()
    diffs = [i for i in range(len(orig)) if orig[i] != new[i]]
    print(f"Bytes modificados: {len(diffs)} (esperado: {len(PATCH)})")
    print(f"SHA-256 parcheado: {sha256(new)}")
    print(f"Escrito en: {dst}")
    if len(diffs) != len(PATCH) or len(orig) != len(new):
        print("ERROR de verificacion: NO uses este archivo.")
        return 1
    print("OK. Copia patched/FT-710_MAIN_V0112.SFL a la SD (sin renombrar).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
