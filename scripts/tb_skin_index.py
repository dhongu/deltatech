#!/usr/bin/env python3
"""
tb_skin_index.py — îmbracă în stil Terrabit fișierele static/description/index.html
generate de oca-gen-addon-readme, FĂRĂ a modifica description.md sau template-ul .jinja.

Cum funcționează:
  1. oca-gen-addon-readme generează README.rst + index.html (docutils, html4css1).
  2. Acest script rulează DUPĂ și, pentru fiecare index.html generat de OCA:
       - injectează un <style> scoped sub .document (rezistă la extragerea body-ului de Odoo);
       - inserează un hero construit din __manifest__.py (nume + summary + versiune);
       - adaugă un bloc de suport/footer Terrabit la final.
  3. Atinge DOAR fișierele generate de OCA (care conțin marcajul "oca-gen-addon-readme"),
     deci index.html-urile scrise manual rămân neatinse.

Idempotent: dacă fișierul a fost deja îmbrăcat (conține marcajul TB), îl sare.

Utilizare:
    python tb_skin_index.py --addons-dir .          # tot repo-ul
    python tb_skin_index.py --addon-dir deltatech_delivery_dpd
"""

import argparse
import ast
import os
import re

TB_MARKER = "<!-- tb-skin v1 -->"

# ---- Paletă & branding (modifică aici o singură dată pentru toate modulele) ----
# Nuanțele oficiale din logo-ul Terrabit (TERRABIT LOGO FULL.svg):
#   #006F42 verde închis, #57B952 verde deschis, alb.
TB = {
    "primary": "#006F42",  # verde închis (brand)
    "dark": "#00432a",  # verde foarte închis (start gradient hero / carduri suport)
    "accent": "#57B952",  # verde deschis (brand)
    "ink": "#1f2937",
    "muted": "#64748b",
    "bg": "#f0f7f2",  # alb cu tentă verde
    "border": "#dbe7df",
    "website": "https://www.terrabit.ro",
    "company": "Terrabit Solutions SRL",
}

# Semnul Terrabit (thumbs-up) ca SVG inline — păstrează nuanțele de brand,
# stă pe un badge alb în hero. Self-contained: nu depinde de fișiere externe.
LOGO_MARK = """<svg class="tb-mark" viewBox="1859 2922 7974 2424" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Terrabit Solutions"><g id="Layer_x0020_1"> <g id="_1723519382240"> <g> <path fill="#006F42" d="M3949.32 4788.01c-198.6,301.96 -540.42,501.36 -928.86,501.36 -187.98,0 -365.02,-46.75 -520.25,-129.17l-274.56 127.74c-42.99,20.04 -94.09,1.44 -114.15,-41.55 -3.31,-7.09 -5.55,-14.4 -6.81,-21.76l-146.13 -718.67c-31.93,-103.56 -49.13,-213.57 -49.13,-327.61 0,-388.45 199.41,-730.28 501.4,-928.88 -236.37,200.26 -386.46,499.21 -386.46,833.26 0,109.11 16.11,217.54 48.24,321.83l0.28 0.91 146.4 719.97 0.04 0.29c1.01,5.84 2.79,11.51 5.3,16.87 15.52,33.29 55.2,47.67 88.48,32.19l283.27 -131.8 8.5 4.51c157.78,83.79 332.57,126.93 511.2,126.93 334.04,0 632.98,-150.07 833.23,-386.42z"/> <path fill="#57B952" d="M3116.09 2971.72c613.59,0 1111.02,497.43 1111.02,1111.02 0,613.59 -497.43,1111.01 -1111.02,1111.01 -187.99,0 -365.04,-46.76 -520.26,-129.18l-274.55 127.75c-42.98,20.04 -94.09,1.44 -114.14,-41.54 -3.3,-7.09 -5.55,-14.41 -6.82,-21.76l-146.15 -718.76c-31.9,-103.53 -49.09,-213.52 -49.09,-327.52 0,-613.59 497.43,-1111.02 1111.02,-1111.02z"/> <path fill="#FEFEFE" d="M2360.94 4098.28l375.82 805.95 -451.69 210.15 -182.2 -896.1 258.07 -120zm428.38 703.91l198.81 -99.11c62.37,83.15 166.89,100.79 340.54,11.09l484.05 -225.72c107.09,-53.21 96.98,-126.68 76.79,-193.9 -2.53,-8.41 -8.07,-14.65 -16.14,-18.13 -8.07,-3.48 -16.3,-3.02 -24.26,0.7l-249.32 116.26 -23.05 -49.43 317.66 -148.13c9.82,-4.58 14.58,-16.35 15.1,-27.18 3.83,-79.3 -26.19,-136.31 -62.48,-168.39 -8.98,-7.94 -21.08,-9.2 -31.95,-4.14l-303.4 141.48 -21.02 -45.07 298.91 -139.39c10.44,-4.87 13.29,-21.8 12.89,-33.33 -2.42,-69.25 -39.92,-137.4 -110.82,-171.6 -8.23,-3.97 -16.91,-3.75 -25.2,0.11l-301.8 140.73 -20.89 -44.79 265.07 -123.6c12.06,-5.63 15.23,-24.96 12.41,-37.97 -24.22,-111.62 -99.13,-146.3 -187.82,-140.43 -17.35,1.14 -348.24,161.26 -393.16,183.33l-166.39 -303.2c-34.86,-54.98 -66.53,-130.89 -163.22,-144.72 -124.71,-17.84 -172.13,55.72 -187.08,119.92 -14.95,64.2 132.15,216.07 162.97,279.65 50.49,108.79 -95.56,187.8 -40.39,364.84l-172.71 82.62 315.9 677.45z"/> </g> <g> <polygon fill="#57B952" points="4730.69,4288.26 9783.46,4288.26 9783.46,4317.07 4730.69,4317.07 "/> <path fill="#006F42" d="M4930.31 4149.13l226.77 0 0 -486.48 199.63 0 0 -191.88 -626.02 0 0 191.88 199.63 0 0 486.48zm477.76 0l583.39 0 0 -186.07 -360.5 0 0 -73.65 331.42 0 0 -163.78 -331.42 0 0 -68.8 355.65 0 0 -186.06 -578.54 0 0 678.35zm644.44 0l226.77 0 0 -193.81 46.52 0 1.94 0 127.92 193.81 258.74 0 -157.96 -230.64c82.37,-39.73 133.73,-108.54 133.73,-207.38l0 -1.94c0,-69.78 -21.32,-120.17 -62.02,-160.87 -47.48,-47.48 -124.04,-77.52 -244.2,-77.52l-331.43 0 0 678.35zm226.77 -355.65l0 -132.76 98.84 0c52.33,0 86.25,21.32 86.25,64.93l0 1.94c0,41.67 -32.95,65.89 -87.21,65.89l-97.88 0zm466.12 355.65l226.77 0 0 -193.81 46.52 0 1.94 0 127.92 193.81 258.74 0 -157.96 -230.64c82.37,-39.73 133.74,-108.54 133.74,-207.38l0 -1.94c0,-69.78 -21.32,-120.17 -62.02,-160.87 -47.48,-47.48 -124.04,-77.52 -244.2,-77.52l-331.43 0 0 678.35zm226.77 -355.65l0 -132.76 98.84 0c52.33,0 86.25,21.32 86.25,64.93l0 1.94c0,41.67 -32.95,65.89 -87.21,65.89l-97.88 0zm392.48 355.65l242.27 0 34.89 -91.09 237.43 0 35.85 91.09 246.15 0 -285.88 -683.2 -224.83 0 -285.88 683.2zm334.33 -251.96l62.02 -164.74 62.02 164.74 -124.04 0zm490.35 251.96l376 0c171.53,0 260.68,-79.46 260.68,-188l0 -1.94c0,-93.04 -56.2,-139.55 -143.42,-164.75 72.68,-25.19 121.13,-74.61 121.13,-155.05l0 -1.94c0,-46.51 -17.44,-81.4 -41.67,-105.63 -39.73,-39.73 -98.85,-61.05 -192.85,-61.05l-379.88 0 0 678.35zm220.95 -411.86l0 -94.97 97.87 0c48.46,0 72.69,16.48 72.69,46.51l0 1.94c0,30.04 -23.26,46.52 -71.71,46.52l-98.85 0zm0 240.33l0 -100.78 114.35 0c49.42,0 73.65,20.35 73.65,49.43l0 1.94c0,29.07 -25.2,49.42 -74.62,49.42l-113.38 0zm467.09 171.53l226.76 0 0 -678.35 -226.76 0 0 678.35zm479.69 0l226.77 0 0 -486.48 199.63 0 0 -191.88 -626.02 0 0 191.88 199.63 0 0 486.48z"/> <path fill="#2b2b2b" d="M5189.5 4697.25l0 -0.96c0,-58.23 -38.19,-82.58 -105.97,-100.24 -57.75,-14.8 -72.07,-21.96 -72.07,-43.91l0 -0.96c0,-16.22 14.8,-29.11 42.96,-29.11 28.16,0 57.28,12.41 86.87,32.93l38.19 -55.37c-33.89,-27.21 -75.42,-42.48 -124.1,-42.48 -68.26,0 -116.95,40.09 -116.95,100.72l0 0.96c0,66.35 43.44,84.96 110.74,102.15 55.85,14.32 67.3,23.87 67.3,42.48l0 0.95c0,19.57 -18.14,31.5 -48.21,31.5 -38.19,0 -69.69,-15.75 -99.76,-40.57l-43.43 52.03c40.09,35.8 91.17,53.46 141.76,53.46 72.08,0 122.68,-37.23 122.68,-103.58zm626.61 -68.26l0 -0.96c0,-94.99 -73.98,-171.84 -177.09,-171.84 -103.1,0 -178.05,77.81 -178.05,172.8l0 0.95c0,94.99 73.99,171.84 177.09,171.84 103.1,0 178.04,-77.8 178.04,-172.79zm-76.85 0.95c0,57.28 -41.05,104.06 -100.24,104.06 -59.19,0 -101.2,-47.74 -101.2,-105.01l0 -0.96c0,-57.28 41.05,-104.06 100.24,-104.06 59.19,0 101.19,47.74 101.19,105.02l0 0.95zm604.67 166.11l0 -66.82 -166.59 0 0 -267.31 -73.51 0 0 334.13 240.1 0zm554.06 -145.58l0 -188.55 -73.51 0 0 191.41c0,52.98 -27.21,80.19 -72.08,80.19 -44.87,0 -72.08,-28.16 -72.08,-82.58l0 -189.02 -73.51 0 0 190.93c0,98.33 54.9,148.44 144.63,148.44 89.74,0 146.54,-49.64 146.54,-150.83zm550.24 -120.77l0 -67.78 -276.85 0 0 67.78 101.67 0 0 266.35 73.51 0 0 -266.35 101.67 0zm355.5 266.35l0 -334.13 -73.51 0 0 334.13 73.51 0zm646.19 -167.06l0 -0.96c0,-94.99 -73.98,-171.84 -177.09,-171.84 -103.1,0 -178.05,77.81 -178.05,172.8l0 0.95c0,94.99 73.99,171.84 177.09,171.84 103.1,0 178.04,-77.8 178.04,-172.79zm-76.85 0.95c0,57.28 -41.05,104.06 -100.24,104.06 -59.19,0 -101.2,-47.74 -101.2,-105.01l0 -0.96c0,-57.28 41.05,-104.06 100.24,-104.06 59.19,0 101.19,47.74 101.19,105.02l0 0.95zm661.47 166.11l0 -334.13 -72.56 0 0 205.73 -156.56 -205.73 -67.78 0 0 334.13 72.56 0 0 -212.41 161.81 212.41 62.53 0zm544.04 -98.8l0 -0.96c0,-58.23 -38.19,-82.58 -105.97,-100.24 -57.75,-14.8 -72.08,-21.96 -72.08,-43.91l0 -0.96c0,-16.22 14.8,-29.11 42.96,-29.11 28.16,0 57.28,12.41 86.87,32.93l38.19 -55.37c-33.89,-27.21 -75.42,-42.48 -124.1,-42.48 -68.26,0 -116.95,40.09 -116.95,100.72l0 0.96c0,66.35 43.43,84.96 110.74,102.15 55.85,14.32 67.3,23.87 67.3,42.48l0 0.95c0,19.57 -18.14,31.5 -48.21,31.5 -38.19,0 -69.69,-15.75 -99.76,-40.57l-43.43 52.03c40.09,35.8 91.17,53.46 141.76,53.46 72.07,0 122.67,-37.23 122.67,-103.58z"/> </g> </g> </g></svg>"""

STYLE = """
<style>%(marker)s
/* ===== Terrabit skin — scoped sub .document ca să reziste la randarea Odoo ===== */
.document{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
  color:%(ink)s;line-height:1.65;max-width:1080px;margin:0 auto;padding:0 8px;}
.document .tb-hero{background:linear-gradient(135deg,%(dark)s 0%%,%(primary)s 100%%);
  color:#fff;border-radius:16px;padding:44px 36px;text-align:center;margin:8px 0 36px;}
.document .tb-hero .tb-brand{display:inline-flex;align-items:center;gap:6px;font-weight:700;
  letter-spacing:.5px;background:rgba(255,255,255,.16);padding:5px 14px;border-radius:999px;
  font-size:11px;margin:0 0 14px;text-transform:uppercase;}
.document .tb-hero h1{font-size:34px;line-height:1.15;margin:0 0 12px;color:#fff;font-weight:800;border:none;}
.document .tb-hero p{font-size:17px;color:#d6ebdd;max-width:680px;margin:0 auto 18px;}
.document .tb-hero .tb-badges{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;}
.document .tb-hero .tb-badge{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.25);
  padding:5px 13px;border-radius:999px;font-size:12px;font-weight:600;}

/* Titlul docutils original — îl ascundem (îl preluăm în hero) */
.document > h1.title{display:none;}
.document > p.subtitle{display:none;}

/* Secțiuni & titluri din conținut (din description.md / fragmente) */
.document .section > h1,.document .section > h2{
  font-size:24px;font-weight:700;color:%(dark)s;margin:34px 0 12px;
  padding-bottom:8px;border-bottom:2px solid %(bg)s;}
.document .section .section > h2,.document .section h3{font-size:18px;color:%(dark)s;margin:20px 0 8px;}

/* Listele de funcții — stilizate ca itemi de card, nu buline plate */
.document ul.simple{list-style:none;padding:0;display:grid;
  grid-template-columns:repeat(2,1fr);gap:12px;}
.document ul.simple > li{background:#fff;border:1px solid %(border)s;border-radius:12px;
  padding:14px 16px 14px 40px;position:relative;}
.document ul.simple > li:before{content:"";position:absolute;left:14px;top:18px;width:14px;height:14px;
  border-radius:4px;background:linear-gradient(135deg,%(primary)s,%(accent)s);}
.document ul.simple ul.simple{display:block;margin-top:8px;}
.document ul.simple ul.simple > li{background:none;border:none;padding:2px 0 2px 18px;}
.document ul.simple ul.simple > li:before{width:6px;height:6px;border-radius:50%%;left:0;top:11px;}

/* Imagini / capturi */
.document img{max-width:100%%;height:auto;border:1px solid %(border)s;border-radius:12px;
  margin:14px 0;box-shadow:0 4px 16px rgba(11,31,58,.06);}
.document a.image-reference img{box-shadow:none;}
/* badge-urile shields.io rămân mici și fără ramă */
.document p > a > img[src*="img.shields.io"],.document img[src*="img.shields.io"]{
  display:inline;border:none;border-radius:4px;margin:2px;box-shadow:none;width:auto;}

/* Tabele (dependențe, compatibilitate) */
.document table{border-collapse:collapse;width:100%%;font-size:14px;margin:14px 0;}
.document table td,.document table th{border:1px solid %(border)s;padding:10px 14px;}
.document table th{background:%(bg)s;}

/* Bloc suport + footer Terrabit (adăugat de script) */
.document .tb-support{background:%(dark)s;color:#fff;border-radius:16px;padding:34px;
  display:flex;gap:24px;align-items:center;justify-content:space-between;flex-wrap:wrap;margin:40px 0 16px;}
.document .tb-support h2{color:#fff;border:none;margin:0 0 6px;font-size:22px;}
.document .tb-support p{color:#cfe6d8;max-width:520px;margin:0;}
.document .tb-support a{display:inline-block;background:#fff;color:%(dark)s;font-weight:700;
  text-decoration:none;padding:12px 26px;border-radius:10px;}
.document .tb-foot{text-align:center;color:%(muted)s;font-size:13px;padding:24px 0 8px;}
.document .tb-foot a{color:%(primary)s;}
.document .tb-foot-logo{display:inline-block;line-height:0;margin-bottom:12px;}
.document .tb-foot-logo .tb-mark{display:block;height:44px;width:auto;}
.document .tb-foot-txt{color:%(muted)s;}

@media(max-width:768px){
  .document ul.simple{grid-template-columns:1fr;}
  .document .tb-hero h1{font-size:26px;}
}
</style>
"""

HERO = """%(marker)s
<div class="tb-hero">
  <span class="tb-brand">Odoo Partner</span>
  <h1>%(name)s</h1>
  %(summary)s
  <div class="tb-badges">
    %(badges)s
  </div>
</div>
"""

SUPPORT = """
<div class="tb-support">
  <div>
    <h2>Need help?</h2>
    <p>We are an Odoo partner building apps for the Romanian market
       (SAGA &amp; WinMentor export; Romanian accounting localization in progress).
       Direct support from the team that built the module.</p>
  </div>
  <a href="%(website)s">Contact Terrabit</a>
</div>
<div class="tb-foot">
  <a href="%(website)s" class="tb-foot-logo">%(logo)s</a>
  <div class="tb-foot-txt">&copy; %(company)s &bull;
    <a href="%(website)s">terrabit.ro</a> &bull; Odoo apps for Romania, Ireland &amp; Moldova</div>
</div>
"""


def read_manifest(addon_dir):
    for fn in ("__manifest__.py", "__openerp__.py"):
        path = os.path.join(addon_dir, fn)
        if os.path.exists(path):
            with open(path, encoding="utf8") as f:
                return ast.literal_eval(f.read())
    return {}


def build_badges(manifest):
    items = []
    # versiune Odoo din 'version' (ex. 19.0.1.0.0 -> 19.0)
    ver = str(manifest.get("version", ""))
    m = re.match(r"(\d+\.\d+)", ver)
    if m:
        items.append(f"Odoo {m.group(1)}")
    items += ["Online &bull; Odoo.sh &bull; On-premise", "Dedicated support"]
    if manifest.get("price"):
        cur = manifest.get("currency", "EUR")
        price = manifest["price"]
        # afișează 249 nu 249.0, dar păstrează zecimalele reale (291.15)
        price_txt = f"{price:g}" if isinstance(price, (int, float)) else str(price)
        items.append(f"{price_txt} {cur}")
    return "\n    ".join(f'<span class="tb-badge">{b}</span>' for b in items)


# Texte de heading care marchează secțiunea în limba secundară (fără diacritice, lowercase).
RO_MARKERS = ("romana", "ro", "romaneste", "limba romana", "descriere ro")


def _strip_diacritics(s):
    table = str.maketrans("ăâîșşțţ", "aaisstt")
    return s.translate(table)


def _section_end(html, start):
    """Întoarce poziția de sfârșit a <div ...> care începe la `start`, prin numărarea div-urilor."""
    depth = 0
    for m in re.finditer(r"<div\b|</div>", html[start:]):
        depth += 1 if m.group(0) != "</div>" else -1
        if depth == 0:
            return start + m.end()
    return None


def strip_toc(html):
    """Elimină TOC-ul local docutils (titlul „Table of contents" + lista) —
    redundant și „developer-looking" pe o pagină de prezentare."""
    html = re.sub(
        r"<p[^>]*>\s*<strong>\s*Table of contents\s*</strong>\s*</p>\s*",
        "",
        html,
        flags=re.I,
    )
    html = re.sub(
        r'<div class="contents[^"]*"[^>]*>.*?</div>\s*',
        "",
        html,
        count=1,
        flags=re.I | re.S,
    )
    return html


def remove_secondary_language(html):
    """Elimină secțiunea în limba secundară (RO) — păstrăm pagina doar în EN."""
    # rulează repetat: pot exista mai multe secțiuni RO (Descriere, Funcții etc.)
    changed = True
    while changed:
        changed = False
        for m in re.finditer(r"<(h[1-6])\b[^>]*>(.*?)</\1>", html, re.I | re.S):
            text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            norm = _strip_diacritics(text).lower().strip()
            if norm in RO_MARKERS or norm.startswith("romana"):
                sec_start = html.rfind('<div class="section"', 0, m.start())
                if sec_start == -1:
                    continue
                sec_end = _section_end(html, sec_start)
                if not sec_end:
                    continue
                html = html[:sec_start] + html[sec_end:]
                changed = True
                break
    return html


def skin_html(html, manifest):
    if TB_MARKER in html:
        return None  # deja procesat
    if "oca-gen-addon-readme" not in html:
        return None  # index.html scris manual -> nu atingem

    name = manifest.get("name") or ""
    summary = manifest.get("summary") or ""
    hero = HERO % {
        "marker": TB_MARKER,
        "logo": LOGO_MARK,
        "name": name,
        "summary": f"<p>{summary}</p>" if summary else "",
        "badges": build_badges(manifest),
    }
    style = STYLE % dict(TB, marker=TB_MARKER)
    support = SUPPORT % dict(TB, logo=LOGO_MARK)

    # injectează style imediat după <body...> (funcție de replace ca să nu interpreteze \ din CSS)
    html = re.sub(r"<body[^>]*>", lambda m: m.group(0) + style, html, count=1)
    # injectează hero imediat după <div class="document"...>
    html = re.sub(r'<div class="document"[^>]*>', lambda m: m.group(0) + hero, html, count=1)
    # elimină secțiunea RO — pagina rămâne doar în EN
    html = remove_secondary_language(html)
    # elimină TOC-ul local docutils
    html = strip_toc(html)
    # adaugă blocul de suport + footer ÎNĂUNTRUL .document, chiar înainte de </div>-ul
    # său de închidere. Esențial: Odoo Apps extrage doar conținutul din .document, iar
    # CSS-ul e scoped sub .document — un bloc plasat la nivel de <body> ar fi și pierdut,
    # și nestilizat.
    doc = re.search(r'<div class="document"[^>]*>', html)
    doc_end = _section_end(html, doc.start()) if doc else None
    if doc_end:
        close = doc_end - len("</div>")
        html = html[:close] + support + "\n" + html[close:]
    elif "</body>" in html:
        html = html.replace("</body>", support + "\n</body>", 1)
    else:
        html += support
    return html


def process(addon_dir):
    index_path = os.path.join(addon_dir, "static", "description", "index.html")
    if not os.path.exists(index_path):
        return False
    with open(index_path, encoding="utf8") as f:
        html = f.read()
    manifest = read_manifest(addon_dir)
    new_html = skin_html(html, manifest)
    if new_html is None:
        return False
    with open(index_path, "w", encoding="utf8") as f:
        f.write(new_html)
    print(f"[tb-skin] {index_path}")
    return True


def find_addons(addons_dir):
    for entry in sorted(os.listdir(addons_dir)):
        d = os.path.join(addons_dir, entry)
        if os.path.isdir(d) and (
            os.path.exists(os.path.join(d, "__manifest__.py")) or os.path.exists(os.path.join(d, "__openerp__.py"))
        ):
            yield d


def main():
    ap = argparse.ArgumentParser(description="Terrabit skin pentru index.html OCA")
    ap.add_argument("--addon-dir", action="append", default=[], help="un singur modul")
    ap.add_argument("--addons-dir", help="director cu mai multe module")
    args = ap.parse_args()

    targets = list(args.addon_dir)
    if args.addons_dir:
        targets += list(find_addons(args.addons_dir))
    if not targets:
        targets = list(find_addons("."))

    count = sum(1 for d in targets if process(d))
    print(f"[tb-skin] gata: {count} module modernizate.")


if __name__ == "__main__":
    main()
