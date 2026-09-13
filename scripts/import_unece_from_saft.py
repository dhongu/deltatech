#!/usr/bin/env python3
# ©  2026 Terrabit Solutions SRL
#    Dorin Hongu <dhongu(@)gmail(.)com>
"""Generează nomenclatorul de coduri UNECE din schema SAF-T publicată de ANAF.

Sursa e fila ``Unitati_masura`` din schema SAF-T publicată de ANAF:
https://static.anaf.ro/static/10/Anaf/Informatii_R/RO_SAFT_SchemaDefCod_16.02.2026.xlsx
Fila listează codurile admise la raportare, cu denumirea în engleză și traducerea
indicativă în română. Fișierul nu e versionat în repo — are 2 MB și se republică
periodic — deci scriptul primește calea lui ca argument.

Scrie două fișiere, din aceeași trecere, ca să nu poată ieși din sincron:

* ``data/uom.unece.code.csv``  — codul, denumirea EN și sursa (rec20/rec21)
* ``i18n/ro.po``              — denumirile RO, ca traduceri ale câmpului ``name``

Denumirile româneşti intră prin mecanismul obișnuit de traducere, nu ca un al
doilea câmp: altfel ``name`` ar fi netradus într-o bază cu altă limbă, iar
nomenclatorul ar avea două surse de adevăr pentru același text.

Traducerile existente din ro.po care NU aparțin nomenclatorului (etichete de
câmpuri, meniuri) sunt păstrate neatinse; scriptul le rescrie doar pe ale
codurilor.

⚠️ ORDINEA CONTEAZĂ. Odoo ia REFERINȚELE traducerilor din ``.pot`` și textele din
``.po``, deci un ``.pot`` rămas în urmă lipește traduceri pe înregistrări greșite,
fără nicio eroare: la prima încărcare a nomenclatorului, ``.pot``-ul vechi încă
lega ``unece_xpf`` de ``msgid "Pallet"``, iar codul XPF („Pen") s-a pomenit numit
„Palet" în română. Fluxul corect, după ce se schimbă datele:

1. rulează scriptul (scrie CSV-ul, și un ro.po care încă nu poate fi verificat)
2. instalează modulul pe o bază curată
3. ``odoo-bin i18n export -d <bază> -o i18n/<modul>.pot <modul>``
4. rulează scriptul din nou, acum peste ``.pot``-ul proaspăt
5. reinstalează cu ``--load-language=ro_RO`` și verifică un cod a cărui denumire
   RO diferă de EN

    python3 scripts/import_unece_from_saft.py ~/Downloads/RO_SAFT_SchemaDefCod_16.02.2026.xlsx
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:  # pragma: no cover
    sys.exit("openpyxl lipsește: pip install openpyxl")

SHEET = "Unitati_masura"
FIRST_DATA_ROW = 12  # rândurile 1-11 sunt copertă, date de publicare și antet

# Corecții față de fișierul ANAF, fiecare cu motivul ei. Nomenclatorul e o sursă
# oficială, dar nu e lipsit de erori, iar noi nu putem propaga mai departe un
# text despre care știm că e greșit.
NAME_RO_FIXES = {
    # „square foot" e tradus în fișier tot prin „metru pătrat", ca FTK să nu iasă
    # identic cu MTK în interfață.
    "FTK": "picior pătrat",
    # Rămase netraduse în fișier.
    "C62": "unu (bucată)",
    # Tradus automat ca „negator": „denier" e unitatea de finețe a firelor
    # textile, nu substantivul englezesc.
    "A49": "denier",
    "M83": "denier",
}

# Coduri care apar de două ori în fișier. Păstrăm varianta marcată ca modificare
# față de publicarea anterioară, deci ultima apariție din filă.
KNOWN_DUPLICATES = {"B30"}


def read_rows(xlsx: Path):
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    if SHEET not in wb.sheetnames:
        sys.exit(f"fila {SHEET!r} lipsește din {xlsx.name}")
    seen, rows = {}, []
    for index, row in enumerate(wb[SHEET].iter_rows(values_only=True), 1):
        if index < FIRST_DATA_ROW or not row[1]:
            continue
        code = str(row[1]).strip()
        source = str(row[0] or "").strip() or "other"
        name_en = (row[2] or "").strip()
        name_ro = (row[3] or "").strip() or name_en
        if not name_en:
            print(f"  ! {code}: fără denumire engleză, sărit")
            continue
        entry = (code, source, name_en, NAME_RO_FIXES.get(code, name_ro))
        if code in seen:
            if code not in KNOWN_DUPLICATES:
                print(f"  ! {code}: duplicat nedocumentat, păstrez ultima apariție")
            rows[seen[code]] = entry
        else:
            seen[code] = len(rows)
            rows.append(entry)
    return rows


def write_csv(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["id", "code", "name", "source"])
        for code, source, name_en, _ in rows:
            writer.writerow([f"unece_{code.lower()}", code, name_en, source])
    print(f"CSV   → {path}  ({len(rows)} coduri)")


def po_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def pot_msgids(path: Path):
    """msgid-urile din .pot, sau None dacă fișierul lipsește."""
    if not path.exists():
        return None
    found = set()
    for block in path.read_text(encoding="utf-8").split("\n\n"):
        match = re.search(r'^msgid ((?:"(?:[^"\\]|\\.)*"\s*)+)', block, re.M)
        if match and "Project-Id-Version" not in block:
            key = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(1)))
            if key:
                found.add(key)
    return found


def write_po(rows, path: Path, module: str, known=None):
    """Rescrie blocurile nomenclatorului, păstrând restul traducerilor.

    Traducerile păstrate se filtrează după .pot: Odoo fuzionează .po cu .pot și
    sare tăcut intrările absente din al doilea, iar o etichetă rămasă de la un
    câmp între timp redenumit ar trece neobservată până când cineva caută de ce
    interfața e pe jumătate în engleză.
    """
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    blocks = existing.split("\n\n") if existing else []
    header = (
        blocks[0]
        if blocks
        else (
            "# Traducerea modulului Odoo.\n"
            "# This file contains the translation of the following modules:\n"
            f"# \t* {module}\n#\n"
            'msgid ""\nmsgstr ""\n'
            '"MIME-Version: 1.0\\n"\n'
            '"Content-Type: text/plain; charset=UTF-8\\n"\n'
            '"Content-Transfer-Encoding: \\n"\n'
            '"Language: ro\\n"\n'
        )
    )
    kept, dropped = [], []
    for block in blocks[1:]:
        if not block.strip() or "model:uom.unece.code," in block:
            continue
        match = re.search(r'^msgid ((?:"(?:[^"\\]|\\.)*"\s*)+)', block, re.M)
        key = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(1))) if match else ""
        if known is not None and key and key not in known:
            dropped.append(key[:60])
            continue
        kept.append(block)
    for key in dropped:
        print(f"  - scot traducerea orfană (absentă din .pot): {key!r}")
    # Un msgid apare o singură dată într-un .po, cu toate referințele grupate sub
    # el: două coduri pot împărți aceeași denumire engleză (A49 și M83 sunt
    # amândouă „denier"), iar un al doilea bloc cu același msgid face fișierul
    # invalid — `msgfmt` îl respinge, și odată cu el toate traducerile modulului.
    by_msgid = {}
    for code, _, name_en, name_ro in rows:
        entry = by_msgid.setdefault(name_en, {"codes": [], "ro": name_ro})
        entry["codes"].append(code)
        if entry["ro"] != name_ro:
            print(f"  ! {name_en!r}: traduceri RO diferite ({entry['ro']!r} vs {name_ro!r}), o păstrez pe prima")
    generated = []
    for name_en, entry in by_msgid.items():
        refs = "".join(f"#: model:uom.unece.code,name:{module}.unece_{code.lower()}\n" for code in entry["codes"])
        generated.append(f'#. module: {module}\n{refs}msgid "{po_escape(name_en)}"\nmsgstr "{po_escape(entry["ro"])}"')
    path.write_text("\n\n".join([header] + kept + generated) + "\n", encoding="utf-8")
    print(f"ro.po → {path}  ({len(generated)} traduceri, {len(kept)} păstrate)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("xlsx", type=Path, help="Schema SAF-T publicată de ANAF (.xlsx)")
    parser.add_argument(
        "--addon-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "deltatech_uom_unece",
        help="Modulul în care se scriu fișierele",
    )
    args = parser.parse_args()
    if not args.xlsx.exists():
        sys.exit(f"nu găsesc {args.xlsx}")

    rows = read_rows(args.xlsx)
    odd = [code for code, *_ in rows if not re.fullmatch(r"[0-9A-Z]{2,4}", code)]
    if odd:
        sys.exit(f"coduri cu format neașteptat: {odd}")
    long_codes = [code for code, *_ in rows if len(code) > 3]
    if long_codes:
        # Schema eTransport (`CodUMType`) acceptă doar 2-3 caractere; le raportăm
        # ca să se știe că nu orice cod din SAF-T e trimisibil pe orice document.
        print(f"  i coduri de 4 caractere, neutilizabile pe eTransport: {long_codes}")

    module = args.addon_dir.name
    write_csv(rows, args.addon_dir / "data" / "uom.unece.code.csv")
    pot = args.addon_dir / "i18n" / f"{module}.pot"
    write_po(rows, args.addon_dir / "i18n" / "ro.po", module, pot_msgids(pot))


if __name__ == "__main__":
    main()
