#!/usr/bin/env python
# scripts/check_po_vs_pot.py
"""Blocheaza traducerile care ar fi ignorate in silentiu de Odoo.

Odoo NU citeste `i18n/<lang>.po` de unul singur: `PoFileReader.__init__` il
fuzioneaza mai intai cu `i18n/<modul>.pot`, ca sa foloseasca referintele `#:`
din .pot (mai actuale decat cele din .po):

    pot_path = get_pot_path(source.name)      # i18n/ro.po -> i18n/<modul>.pot
    if pot_path:
        self.pofile.merge(polib.pofile(pot_path))

`polib.merge()` are semantica lui `msgmerge`: marcheaza **obsolete** orice
intrare din .po care nu exista in .pot, iar `__iter__` face
`if entry.obsolete: continue`. Efect: **orice msgid tradus in .po dar absent
din .pot este sarit in tacere.**

Nimic nu semnaleaza problema: Odoo logheaza `loading translation file ...
ro.po`, `msgfmt -c` e curat, referintele `#:` sunt corecte, iar traducerile
VECHI functioneaza - doar cele noi nu, pentru ca doar ele lipsesc din .pot.

Hook-ul verifica DOAR intrarile adaugate in commit-ul curent (fata de HEAD),
ca sa nu blocheze commituri din cauza vechiturilor deja existente in .po:
un .po poate contine, legitim, traduceri pentru termeni ai altor module sau
termeni morti, care nu vor aparea niciodata in .pot-ul propriu.

Un modul FARA .pot nu e afectat (fuziunea nu are loc), deci trece.

Reparare, cand hook-ul se plange: regenereaza .pot. `--i18n-export` nu mai
exista in Odoo 19, deci prin shell-ul Odoo, cu modulul instalat:

    m = env["ir.module.module"].search([("name", "=", "<modul>")])
    w = env["base.language.export"].create(
        {"format": "po", "modules": [(6, 0, m.ids)], "lang": "__new__"})
    w.act_getfile()
    open("<modul>/i18n/<modul>.pot", "wb").write(base64.b64decode(w.data))

Atentie la doua capcane ale regenerarii:
  - exportul reflecta ce e INSTALAT in baza: termenii contribuiti prin module
    frati neinstalati nu ies, deci rescrierea poate SARACI .pot. Scrie uniunea
    nou + vechi (un msgid in plus in .pot e inofensiv, unul lipsa anuleaza
    traducerea);
  - regenerarea schimba segmentarea termenilor de view (iconita `<i .../>` se
    fuzioneaza cu `<span>`-ul intr-un singur msgid), deci .po trebuie
    resincronizat, altfel apar orfane noi.
"""

# pylint: disable=print-used
# `print` este interfata unui hook de pre-commit: pre-commit capteaza stdout/stderr
# si le arata utilizatorului. Un logger nu ar aparea nicaieri.
import os
import subprocess
import sys

import polib

MAX_AFISATE = 12


def versiune_din_head(cale):
    """Contine .po-ul din HEAD, sau None daca fisierul e nou in acest commit."""
    director = os.path.dirname(cale) or "."
    radacina = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=director,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not radacina:
        return None
    rel = os.path.relpath(os.path.abspath(cale), radacina)
    rezultat = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=radacina, capture_output=True, text=True)
    if rezultat.returncode != 0:
        return None
    return rezultat.stdout


def traduse(pofile):
    return {e.msgid for e in pofile if e.msgid and e.msgstr and not e.obsolete}


def verifica(cale_po):
    """Intoarce lista msgid-urilor adaugate acum care ar fi ignorate de Odoo."""
    i18n = os.path.dirname(cale_po)
    modul = os.path.basename(os.path.dirname(i18n))
    cale_pot = os.path.join(i18n, modul + ".pot")
    if not os.path.exists(cale_pot):
        return []  # fara .pot nu se face fuziunea, deci nu se pierde nimic

    try:
        ids_pot = {e.msgid for e in polib.pofile(cale_pot)}
        noi = traduse(polib.pofile(cale_po))
    except OSError as e:
        print(f"{cale_po}: nu s-a putut citi ({e})", file=sys.stderr)
        return []

    vechi_txt = versiune_din_head(cale_po)
    if vechi_txt is not None:
        try:
            noi -= traduse(polib.pofile(vechi_txt))
        except Exception as e:  # noqa: BLE001 - versiunea din HEAD e nevalida
            # Nu putem calcula ce s-a adaugat acum, deci verificam TOT fisierul:
            # mai bine un fals pozitiv explicat decat o traducere pierduta tacut.
            print(f"{cale_po}: versiunea din HEAD nu se poate citi ({e}); verific tot fisierul", file=sys.stderr)

    return sorted(noi - ids_pot)


def main(argv):
    probleme = {}
    for cale in argv:
        lipsa = verifica(cale)
        if lipsa:
            probleme[cale] = lipsa
    if not probleme:
        return 0

    print("Traduceri care ar fi IGNORATE in silentiu de Odoo:\n", file=sys.stderr)
    for cale, lipsa in probleme.items():
        modul = os.path.basename(os.path.dirname(os.path.dirname(cale)))
        print(f"  {cale} ({len(lipsa)} intrari absente din {modul}.pot):", file=sys.stderr)
        for msgid in lipsa[:MAX_AFISATE]:
            print(f"      {msgid[:96]!r}", file=sys.stderr)
        if len(lipsa) > MAX_AFISATE:
            print(f"      ... si alte {len(lipsa) - MAX_AFISATE}", file=sys.stderr)
        print(file=sys.stderr)
    print(
        "Cauza: Odoo fuzioneaza .po cu .pot si marcheaza obsolete (deci sare)\n"
        "intrarile absente din .pot. Traducerile de mai sus nu vor ajunge NICIODATA\n"
        "in baza de date, desi fisierul pare corect si msgfmt nu se plange.\n"
        "Reparare: regenereaza i18n/<modul>.pot (vezi antetul scripts/check_po_vs_pot.py).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
