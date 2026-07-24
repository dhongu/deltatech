#!/usr/bin/env python3
"""
tb_skin_index.py — îmbracă în stil Terrabit fișierele static/description/index.html
generate de oca-gen-addon-readme, FĂRĂ a modifica description.md sau template-ul .jinja.

v5 — DESIGN PE BOOTSTRAP (de ce):
  Odoo Apps Store încarcă Bootstrap 5 în bundle-ul frontend (web.assets_frontend.min.css)
  și PĂSTREAZĂ atributul `class` la sanitizare. Deci clasele Bootstrap (`row`, `col`,
  `d-flex`, `border`, `rounded-4`, `text-white`, `fw-bold`, utilitare de spațiere…) sunt
  disponibile ȘI stilizate pe pagina de modul. Confirmat pe store real (`.row`→flex,
  `.bg-success`→verde, `.border`→theme-aware, `.rounded-4`→24px).

  Ce face în continuare sanitizer-ul (deci evităm):
    - ȘTERGE <style>            → niciun CSS din bloc <style>; folosim clase + inline;
    - DESPACHETEAZĂ <div class="document">;
    - ȘTERGE <svg> inline       → logo doar ca <img> absolut sau wordmark text;
    - TAIE `background:`/gradient din inline (supraviețuiește DOAR `background-color`).

  Strategie v5:
    - LAYOUT & TEMĂ prin clase Bootstrap: grilă responsivă (`row`/`col`), flex, spațiere,
      borduri și colțuri theme-aware. TEXTUL NU primește `color` → moștenește culoarea
      temei (Bootstrap `--bs-body-color`): închis pe store (light), deschis pe o gazdă
      dark. Astfel titlurile de secțiune sunt lizibile pe orice temă (spre deosebire de
      v4, care forța `color:#1f2d27` pe tot conținutul și dispărea pe dark).
    - BRAND (hero, bloc suport, CTA, badge-uri, bară-accent, bifă) = `background-color`
      SOLID verde Terrabit inline (Bootstrap `.bg-success` e alt verde) — identic pe orice
      temă. REGULĂ DE AUR: verdele DOAR ca fundal/bordură, niciodată singura sursă de
      lizibilitate a textului.
  Validează cu scripts/tb_apps_preview.py (light + dark), care încarcă Bootstrap și
  comută `data-bs-theme`.

Cum funcționează:
  1. oca-gen-addon-readme generează README.rst + index.html (docutils).
  2. Acest script rulează DUPĂ și, pentru fiecare index.html generat de OCA:
       - ȘTERGE titlul docutils + heading-ul-secțiune duplicat (= numele modulului);
       - elimină badge-urile shields, secțiunea RO, TOC-ul local și changelog-ul;
       - inserează un HERO (verde brand) construit din __manifest__.py;
       - stilizează heading-urile (bară-accent verde), listele de funcții (carduri
         Bootstrap responsive), chip-urile de cod și paragraful lead;
       - adaugă un bloc de suport + footer Terrabit la final.
  3. Atinge DOAR fișierele generate de OCA (care conțin marcajul "oca-gen-addon-readme").

Idempotent: dacă fișierul a fost deja îmbrăcat (conține marcaj tb-skin), îl sare.
Re-skin: regenerează întâi cu oca-gen-addon-readme (șterge marcajul), apoi rulează scriptul.

Utilizare:
    python3 tb_skin_index.py --addons-dir .          # tot repo-ul
    python3 tb_skin_index.py --addon-dir deltatech_delivery_status
"""

import argparse
import ast
import os
import re

TB_MARKER = "<!-- tb-skin v5 -->"
# orice marcaj tb-skin (v1, v2, …) — ca să nu re-îmbrăcăm un fișier deja procesat
ANY_TB_MARKER = re.compile(r"<!-- tb-skin v\d+ -->")

# ---- Paletă & branding (modifică aici o singură dată pentru toate modulele) ----
# Nuanțele oficiale din logo-ul Terrabit: #006F42 verde închis, #57B952 verde deschis.
TB = {
    "primary": "#006F42",  # verde închis (brand) — DOAR pe fundal solid/border
    "dark": "#00432a",  # verde foarte închis (hero pill / bloc suport)
    "accent": "#57B952",  # verde deschis (brand) — bare-accent, bife
    "website": "https://www.terrabit.ro",
    "company": "Terrabit Solutions SRL",
    # Logo opțional găzduit absolut (Odoo elimină SVG inline). Dacă e gol, footer-ul
    # folosește un wordmark text alb pe blocul verde (mereu funcționează).
    "logo_url": "",
}

FONT = "'Segoe UI','Avenir Next','Helvetica Neue',Arial,sans-serif"

# ----------------------------------------------------------------------------- #
# Fragmente HTML — LAYOUT/TEMĂ prin clase Bootstrap; brand-ul verde prin `background-color`
# inline (singurul care supraviețuiește sanitizarea). Textul NU are `color` → moștenește tema.
# ----------------------------------------------------------------------------- #

WRAP_OPEN = f'<div class="mx-auto px-3" style="max-width:1100px;font-family:{FONT};">'

HERO = """%(marker)s
<div class="text-white text-center rounded-4 shadow px-4 py-5 mt-2 mb-4" style="background-color:%(primary)s;">
  <span class="d-inline-block rounded-pill fw-bold text-uppercase mb-4"
    style="background-color:%(dark)s;color:#9be8b6;letter-spacing:1.5px;padding:7px 18px;font-size:11px;">Odoo Partner &nbsp;&bull;&nbsp; Terrabit</span>
  <h1 class="text-white fw-bold mb-3" style="font-size:42px;line-height:1.08;letter-spacing:-0.5px;border:none;">%(name)s</h1>
  %(summary)s
  <div>
    %(badges)s
  </div>
</div>
"""

SUMMARY = '<p class="mx-auto mb-4" style="font-size:19px;color:#cdeccf;max-width:620px;line-height:1.5;">%s</p>'

BADGE = (
    '<span class="d-inline-block rounded-pill fw-semibold text-white m-1"'
    ' style="background-color:%(dark)s;padding:8px 16px;font-size:12px;">%(t)s</span>'
)
BADGE_ACCENT = (
    '<span class="d-inline-block rounded-pill fw-bold m-1"'
    ' style="background-color:%(accent)s;color:#04331f;padding:8px 16px;font-size:12px;">%(t)s</span>'
)

# Container de conținut: fără background/color -> textul moștenește tema Bootstrap.
PANEL_OPEN = '<div class="py-2" style="font-size:16px;line-height:1.65;">'
PANEL_CLOSE = "</div>"

# Bloc de suport + footer: BRAND solid verde închis (theme-independent), include footer-ul.
SUPPORT = """
<div class="text-white text-center rounded-4 px-4 pt-5 pb-4 mt-4 mb-3" style="background-color:%(dark)s;">
  <h2 class="text-white fw-bold mb-2" style="font-size:26px;letter-spacing:-0.3px;border:none;">Need help getting started?</h2>
  <p class="mx-auto mb-4" style="color:#bfe3cc;max-width:600px;line-height:1.6;font-size:16px;">
     We are an Odoo partner building apps for the Romanian market (SAGA &amp; WinMentor
     export; Romanian accounting localization in progress). Direct support from the team
     that built the module.</p>
  <a href="%(website)s" class="d-inline-block fw-bold text-decoration-none rounded-3"
     style="background-color:%(accent)s;color:#04331f;padding:14px 32px;font-size:15px;">Contact Terrabit &rarr;</a>
  <div class="mx-auto mt-4 pt-3" style="border-top:1px solid rgba(255,255,255,0.18);max-width:760px;">
    %(logo)s
    <div class="mt-1" style="color:#bfe3cc;font-size:13px;">
      &copy; %(company)s &nbsp;&bull;&nbsp;
      <a href="%(website)s" class="text-white text-decoration-none fw-semibold">terrabit.ro</a>
      &nbsp;&bull;&nbsp; Odoo apps for Romania, Ireland &amp; Moldova
    </div>
  </div>
</div>
"""


def logo_html():
    """Wordmark footer pe blocul verde închis: <img> absolut dacă e configurat, altfel text alb."""
    if TB["logo_url"]:
        return (
            f'<div><img src="{TB["logo_url"]}" alt="{TB["company"]}" '
            'style="height:34px;width:auto;border:none;"/></div>'
        )
    return '<div class="text-white fw-bold" style="font-size:19px;letter-spacing:2px;">TERRABIT</div>'


def read_manifest(addon_dir):
    for fn in ("__manifest__.py", "__openerp__.py"):
        path = os.path.join(addon_dir, fn)
        if os.path.exists(path):
            with open(path, encoding="utf8") as f:
                return ast.literal_eval(f.read())
    return {}


def build_badges(manifest):
    items = []
    ver = str(manifest.get("version", ""))
    m = re.match(r"(\d+\.\d+)", ver)
    if m:
        items.append((BADGE, f"Odoo {m.group(1)}"))
    items.append((BADGE, "Online &bull; Odoo.sh &bull; On-premise"))
    items.append((BADGE_ACCENT, "Optional support"))
    return "\n    ".join(tmpl % dict(TB, t=t) for tmpl, t in items)


# Texte de heading care marchează secțiunea în limba secundară (fără diacritice, lowercase).
RO_MARKERS = ("romana", "romaneste", "limba romana", "descriere ro", "versiune in romana")


def _strip_diacritics(s):
    table = str.maketrans("ăâîșşțţ", "aaisstt")
    return s.translate(table)


def _norm(text):
    return _strip_diacritics(re.sub(r"<[^>]+>", "", text)).lower().strip()


def _section_end(html, start):
    """Întoarce poziția de sfârșit a <div ...> care începe la `start`, prin numărarea div-urilor."""
    depth = 0
    for m in re.finditer(r"<div\b|</div>", html[start:]):
        depth += 1 if m.group(0) != "</div>" else -1
        if depth == 0:
            return start + m.end()
    return None


def strip_shields(html):
    """Elimină paragraful cu badge-urile shields.io (maturity / github) — clutter OCA."""
    return re.sub(r"<p>(?:(?!</p>).)*?shields\.io.*?</p>\s*", "", html, count=1, flags=re.S)


def remove_docutils_title(html):
    """Șterge titlul/subtitlul docutils duplicat (îl preluăm în hero)."""
    html = re.sub(r'<h1 class="title">.*?</h1>\s*', "", html, count=1, flags=re.S)
    html = re.sub(r'<p class="subtitle">.*?</p>\s*', "", html, count=1, flags=re.S)
    return html


def remove_duplicate_name_heading(html, name):
    """Șterge heading-ul-secțiune al cărui text == numele modulului (duplicat al hero-ului).
    Păstrează conținutul secțiunii (intro), scoate doar heading-ul gol."""
    target = _norm(name)
    if not target:
        return html

    def repl(m):
        return "" if _norm(m.group(2)) == target else m.group(0)

    return re.sub(r"<(h[1-3])\b[^>]*>(.*?)</\1>\s*", repl, html, count=1, flags=re.S)


def strip_toc(html):
    """Elimină TOC-ul local docutils („Table of contents" + lista)."""
    html = re.sub(r"<p[^>]*>\s*<strong>\s*Table of contents\s*</strong>\s*</p>\s*", "", html, flags=re.I)
    html = re.sub(r'<div class="contents[^"]*"[^>]*>.*?</div>\s*', "", html, count=1, flags=re.I | re.S)
    return html


def remove_secondary_language(html):
    """Elimină secțiunea în limba secundară (RO) — păstrăm pagina doar în EN."""
    changed = True
    while changed:
        changed = False
        for m in re.finditer(r"<(h[1-6])\b[^>]*>(.*?)</\1>", html, re.I | re.S):
            norm = _norm(m.group(2))
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


def remove_changelog(html):
    """Elimină secțiunea Changelog (din HISTORY.md) + subsecțiunile de versiune.
    Taie de la <div class="section" id="changelog"> până la secțiunea Bug Tracker
    (pe care o păstrăm). Pe Apps Store istoricul lung nu-și are locul în descriere."""
    start = re.search(r'<div class="section" id="changelog', html)
    if not start:
        return html
    bug = re.search(r'<div class="section" id="bug-tracker"', html[start.start() :])
    if bug:
        end = start.start() + bug.start()
    else:
        end = _section_end(html, start.start()) or len(html)
    return html[: start.start()] + html[end:]


# --- heading-uri docutils: bară-accent verde + text moștenit (theme-aware) ----- #
def style_headings(html):
    """Stilează heading-urile de secțiune (h1/h2/h3 docutils) cu o bară-accent verde la
    stânga + text îngroșat. FĂRĂ `color` -> moștenește tema (lizibil pe light ȘI dark)."""
    sizes = {"h1": 27, "h2": 24, "h3": 19}

    def repl(m):
        tag, inner = m.group(1).lower(), m.group(2)
        # docutils înfășoară heading-urile în <a class="toc-backref"> când există un TOC
        # -> dezvelește-o (păstrează textul), altfel rămâne albastru de link.
        inner = re.sub(r"<a\b[^>]*toc-backref[^>]*>(.*?)</a>", r"\1", inner, flags=re.I | re.S)
        size = sizes.get(tag, 22)
        style = (
            f"border:none;border-left:4px solid {TB['accent']};padding-left:16px;"
            f"font-size:{size}px;letter-spacing:-0.3px;line-height:1.2;"
        )
        return f'<{tag} class="fw-bold mt-4 mb-3" style="{style}">{inner}</{tag}>'

    return re.sub(r"<(h[1-3])\b[^>]*>(.*?)</\1>", repl, html, flags=re.I | re.S)


def style_code(html):
    """Chip pentru cod inline docutils (<tt class="docutils literal">…</tt>).
    Bordură + colțuri Bootstrap (theme-aware), fără fundal -> lizibil pe orice temă."""
    html = re.sub(
        r'<tt class="docutils literal">(.*?)</tt>',
        r'<code class="border rounded px-2" style="font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;">\1</code>',
        html,
        flags=re.S,
    )
    return html


def style_lead_paragraph(html):
    """Primul paragraf „gol" (intro) → lead mai mare (culoare moștenită).
    Rulează DUPĂ ce am scos shields/title."""
    return re.sub(
        r"<p>",
        '<p class="mb-4" style="font-size:19px;line-height:1.6;max-width:780px;opacity:0.92;">',
        html,
        count=1,
    )


# --- carduri de funcții (grilă Bootstrap responsivă) ------------------------- #
# ul = rând Bootstrap cu 1 coloană pe mobil, 2 pe md+. Fiecare item = <li class="col">.
UL_GRID = "list-unstyled row row-cols-1 row-cols-md-2 g-3 mt-1 mb-4"
CARD = "border rounded-3 p-3 h-100"  # theme-aware: bordură + colțuri Bootstrap
BADGE_TICK = "flex-shrink-0 text-center fw-bold rounded d-inline-block"
BADGE_TICK_STYLE = (
    f"background-color:{TB['accent']};color:#04331f;width:22px;height:22px;line-height:22px;font-size:13px;"
)
SUB_UL = "ps-3 mt-2"
SUB_LI = "small"


def _ul_end(html, start):
    depth = 0
    for m in re.finditer(r"<ul\b|</ul>", html[start:]):
        depth += 1 if m.group(0) != "</ul>" else -1
        if depth == 0:
            return start + m.end()
    return None


def _split_top_li(inner):
    items, depth, li_open = [], 0, None
    for m in re.finditer(r"<ul\b[^>]*>|</ul>|<li\b[^>]*>|</li>", inner):
        t = m.group(0)
        if t.startswith("<ul"):
            depth += 1
        elif t == "</ul>":
            depth -= 1
        elif t.startswith("<li") and depth == 0 and li_open is None:
            li_open = m.start()
        elif t == "</li>" and depth == 0 and li_open is not None:
            items.append((li_open, m.end()))
            li_open = None
    return items


def _style_sublists(content):
    content = re.sub(r"<ul\b[^>]*>", f'<ul class="{SUB_UL}">', content)
    content = re.sub(r"<li\b[^>]*>", f'<li class="{SUB_LI}">', content)
    return content


def _render_cards(inner, top):
    parts = []
    for s, e in top:
        cm = re.match(r"<li\b[^>]*>(.*)</li>\s*$", inner[s:e], re.S)
        raw = cm.group(1) if cm else inner[s:e]
        # listă „definiție": <li> care începe cu <strong>lead</strong>: detaliu
        dm = re.match(r"\s*<strong>(.*?)</strong>\s*:?\s*(.*)$", raw, re.S)
        if dm:
            lead = dm.group(1).strip()
            rest = _style_sublists(dm.group(2).strip())
            parts.append(
                f'<li class="col"><div class="{CARD}">'
                f'<span class="fw-bold">{lead}</span>'
                f'<div class="mt-1">{rest}</div></div></li>'
            )
        else:
            content = _style_sublists(raw)
            parts.append(
                f'<li class="col"><div class="{CARD} d-flex gap-2">'
                f'<span class="{BADGE_TICK}" style="{BADGE_TICK_STYLE}">&#10003;</span>'
                f"<div>{content}</div></div></li>"
            )
    return "".join(parts)


def style_feature_lists(html):
    """Transformă listele `ul.simple` (≥3 itemi de nivel superior) în carduri Bootstrap.
    Itemii cu lead bold (<strong>…</strong>: …) devin carduri-definiție; restul, carduri cu bifă.
    Listele scurte (Authors/Maintainers) rămân plate."""
    repls = []
    for m in re.finditer(r'<ul class="simple">', html):
        end = _ul_end(html, m.start())
        if end is None:
            continue
        inner = html[m.end() : end - len("</ul>")]
        top = _split_top_li(inner)
        if len(top) < 3:
            continue
        new_block = f'<ul class="{UL_GRID}">{_render_cards(inner, top)}</ul>'
        repls.append((m.start(), end, new_block))
    for s, e, nb in reversed(repls):
        html = html[:s] + nb + html[e:]
    return html


def skin_html(html, manifest):
    if ANY_TB_MARKER.search(html):
        return None  # deja procesat
    if "oca-gen-addon-readme" not in html:
        return None  # index.html scris manual -> nu atingem

    name = manifest.get("name") or ""
    summary = manifest.get("summary") or ""
    hero = HERO % dict(
        TB,
        marker=TB_MARKER,
        name=name,
        summary=(SUMMARY % summary) if summary else "",
        badges=build_badges(manifest),
    )
    support = SUPPORT % dict(TB, logo=logo_html())

    # 1) curăță: shields, titlu docutils, heading duplicat (= numele), RO, TOC, changelog
    html = strip_shields(html)
    html = remove_docutils_title(html)
    html = remove_duplicate_name_heading(html, name)
    html = remove_secondary_language(html)
    html = strip_toc(html)
    html = remove_changelog(html)
    # 2) stilizează conținutul docutils
    html = style_headings(html)
    html = style_code(html)
    html = style_feature_lists(html)
    html = style_lead_paragraph(html)
    # 3) injectează HERO + deschide PANOUL imediat după <div class="document"> (sau <body>)
    panel_open = PANEL_OPEN % TB
    inject = hero + "\n" + panel_open
    if re.search(r'<div class="document"[^>]*>', html):
        html = re.sub(r'<div class="document"[^>]*>', lambda m: m.group(0) + WRAP_OPEN + inject, html, count=1)
    else:
        html = re.sub(r"<body[^>]*>", lambda m: m.group(0) + WRAP_OPEN + inject, html, count=1)
    # 4) închide PANOUL + adaugă suport/footer + închide wrapper, înainte de </div>.document (sau </body>)
    tail = PANEL_CLOSE + support + "\n</div>\n"  # </div> = închide WRAP_OPEN
    doc = re.search(r'<div class="document"[^>]*>', html)
    doc_end = _section_end(html, doc.start()) if doc else None
    if doc_end:
        close = doc_end - len("</div>")
        html = html[:close] + tail + html[close:]
    elif "</body>" in html:
        html = html.replace("</body>", tail + "</body>", 1)
    else:
        html += tail
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
