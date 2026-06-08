#!/usr/bin/env python3
"""
tb_apps_preview.py — emulează ce face sanitizer-ul Odoo Apps Store cu un index.html
și randează rezultatul pe fundal LIGHT și DARK, ca să poți valida designul LOCAL,
fără să urci la fiecare iterație pe store.

De ce e necesar:
  Odoo Apps Store NU randează index.html ca atare. Îl trece printr-un sanitizer și îl
  pune într-o pagină cu temă (light SAU dark) pe care noi NU o controlăm. Empiric, store-ul:
    - ȘTERGE <style>...</style>            (orice CSS dintr-un bloc <style> dispare);
    - DESPACHETEAZĂ <div class="document"> (selectoarele .document … nu mai potrivesc);
    - ȘTERGE <svg> inline                  (logo SVG inline dispare);
    - TAIE `background:`/`linear-gradient` din style inline (supraviețuiește doar
      `background-color` solid).
  Vezi antetul lui tb_skin_index.py.

Test „worst-case" pentru dark:
  Shell-ul DARK folosește fundal închis ȘI culoare de text implicită ÎNCHISĂ. Astfel,
  orice text fără panou solid + culoare proprie devine invizibil — exact cum pățim pe
  store. Un design care e lizibil și în shell-ul DARK e robust pe ORICE temă Odoo.

Utilizare:
    python3 scripts/tb_apps_preview.py <modul>/static/description/index.html
    # scrie alături:  index.apps-light.html  și  index.apps-dark.html
    # apoi deschide-le (sau prin Preview MCP) și fă screenshot.

    python3 scripts/tb_apps_preview.py <index.html> --report
    # listează doar elementele cu risc pe dark (text fără background propriu).
"""

import argparse
import os
import re
import sys

# ---- Reguli sanitizer (un singur loc; calibrează-le dacă urci o dată pe store real) ----


def sanitize_like_apps_store(html):
    """Aplică transformările observate ale sanitizer-ului Apps Store."""
    # 1) scoate blocurile <style>
    html = re.sub(r"<style\b[^>]*>.*?</style>", "", html, flags=re.I | re.S)
    # 2) scoate <svg> inline
    html = re.sub(r"<svg\b[^>]*>.*?</svg>", "", html, flags=re.I | re.S)
    # 3) despachetează wrapper-ul .document (scoate doar tag-urile div, păstrează conținutul)
    html = re.sub(r'<div class="document"[^>]*>', "", html, count=1, flags=re.I)
    # (perechea </div> e lăsată — irelevantă pentru randare; sanitizer-ul real o scoate)
    # 4) taie `background:` și gradient din style inline; păstrează background-color
    html = re.sub(r"style=\"([^\"]*)\"", _clean_style, html)
    html = re.sub(r"style='([^']*)'", lambda m: _clean_style(m, q="'"), html)
    return html


def _clean_style(m, q='"'):
    decls = []
    for decl in m.group(1).split(";"):
        if not decl.strip():
            continue
        prop = decl.split(":", 1)[0].strip().lower()
        val = decl.split(":", 1)[1].lower() if ":" in decl else ""
        # `background` shorthand și orice gradient sunt eliminate de store
        if prop == "background":
            continue
        if "linear-gradient" in val or "radial-gradient" in val:
            continue
        decls.append(decl.strip())
    return f"style={q}{';'.join(decls)}{q}"


# ---- Raport de risc pe dark: text fără panou solid -------------------------------------

NAKED_TEXT = re.compile(r"<(p|h[1-6]|li|td|span|a)\b([^>]*)>", re.I)


def risk_report(html):
    """Întoarce liniile cu text care NU stă pe un background-color propriu și nici nu are
    o culoare explicită lizibilă -> risc de invizibilitate pe dark."""
    issues = []
    for m in NAKED_TEXT.finditer(html):
        tag, attrs = m.group(1).lower(), m.group(2)
        style = ""
        sm = re.search(r"style=[\"']([^\"']*)[\"']", attrs)
        if sm:
            style = sm.group(1).lower()
        has_bg = "background-color" in style
        has_color = "color:" in style
        # un element pe panou propriu (bg) e ok; unul cu doar culoare proprie e ok DOAR
        # dacă culoarea e deschisă (improbabil să verificăm aici) -> îl marcăm informativ
        if not has_bg and not has_color:
            issues.append((tag, "fără bg & fără color (moștenește tema)"))
        elif not has_bg and has_color:
            issues.append((tag, f"culoare proprie fără panou: {style[:60]}"))
    return issues


# ---- Shell-uri de previzualizare -------------------------------------------------------

SHELL = """<!doctype html><html><head><meta charset="utf-8">
<title>Apps Store preview — %(mode)s</title></head>
<body style="margin:0;background-color:%(bg)s;color:%(fg)s;">
<div style="max-width:1180px;margin:0 auto;padding:24px;">
<div style="font:600 13px -apple-system,Segoe UI,Roboto,sans-serif;color:%(fg)s;opacity:.6;padding:8px 0 16px;">
  Apps Store sanitized preview — %(mode)s theme</div>
%(body)s
</div></body></html>"""

# Trei scenarii:
#  light      — gazdă deschisă (Apps Store public, mereu alb);
#  dark       — WORST-CASE: fundal închis + text implicit ÎNCHIS (gazdă „ostilă");
#  dark-sane  — gazdă dark normală: fundal închis + text implicit DESCHIS.
# Design FORȚAT (panou solid) trebuie să treacă „dark" (worst-case).
# Design ADAPTIV (text moștenit) trebuie să treacă „dark-sane" + „light".
MODES = {
    "light": {"bg": "#ffffff", "fg": "#111111"},
    "dark": {"bg": "#15171a", "fg": "#2b2f36"},
    "dark-sane": {"bg": "#15171a", "fg": "#e8eaed"},
}


def render(html, mode):
    return SHELL % dict(MODES[mode], mode=mode, body=html)


def main():
    ap = argparse.ArgumentParser(description="Emulează sanitizer-ul Apps Store + preview light/dark")
    ap.add_argument("index_html", help="cale către static/description/index.html")
    ap.add_argument("--report", action="store_true", help="doar raportul de risc pe dark")
    args = ap.parse_args()

    if not os.path.exists(args.index_html):
        sys.exit(f"nu există: {args.index_html}")
    raw = open(args.index_html, encoding="utf8").read()
    sanitized = sanitize_like_apps_store(raw)

    if args.report:
        issues = risk_report(sanitized)
        if not issues:
            print("[ok] niciun text fără panou/culoare proprie — dark-proof.")
        else:
            print(f"[risc dark] {len(issues)} elemente fără panou solid:")
            for tag, why in issues:
                print(f"  <{tag}> — {why}")
        return

    base = args.index_html.rsplit(".", 1)[0]
    for mode in MODES:
        out = f"{base}.apps-{mode}.html"
        open(out, "w", encoding="utf8").write(render(sanitized, mode))
        print(f"[preview] {out}")


if __name__ == "__main__":
    main()
