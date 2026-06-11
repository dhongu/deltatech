#!/usr/bin/env python3
"""
tb_skin_index.py — îmbracă în stil Terrabit fișierele static/description/index.html
generate de oca-gen-addon-readme, FĂRĂ a modifica description.md sau template-ul .jinja.

IMPORTANT (de ce folosim STILURI INLINE + DESIGN ADAPTIV LA TEMĂ):
  Odoo Apps Store NU randează index.html ca atare — îl trece printr-un sanitizer care:
    - ȘTERGE tag-urile <style>            (orice CSS dintr-un bloc <style> dispare);
    - DESPACHETEAZĂ <div class="document"> (selectoarele .document … nu mai potrivesc);
    - ȘTERGE <svg> inline                 (un logo SVG inline dispare);
    - TAIE `background:`/`linear-gradient` din style inline (supraviețuiește DOAR
      `background-color` solid; `box-shadow`, `border`, `rgba(...)` supraviețuiesc).
  În plus, pagina e randată pe o TEMĂ pe care NU o controlăm (light SAU dark) și NU o
  putem detecta (media queries / <style> / JS sunt toate tăiate).

  Concluzie (v4 — ADAPTIV LA TEMĂ): nu putem ramifica pe temă, deci:
    - BRAND-ul (hero, CTA, badge-uri, bară-accent, bifă) = `background-color` SOLID verde
      sau border — arată identic pe orice temă (verdele merge pe ambele);
    - CONȚINUTUL (paragrafe, heading-uri, carduri) NU forțează `background-color`/`color`
      pe text → MOȘTENEȘTE culoarea temei gazdă (pe dark devine deschis, pe light închis).
  REGULĂ DE AUR: verdele e folosit DOAR ca fundal solid sau border, NICIODATĂ ca singura
  sursă de lizibilitate a textului (#006F42 e invizibil pe dark, #57B952 are contrast slab
  pe alb). Cardurile au fundal transparent + border `rgba()` vizibil pe ambele teme.
  Presupune o gazdă „sănătoasă" (text deschis pe dark). Validează cu
  scripts/tb_apps_preview.py modurile `light` + `dark-sane`.

Cum funcționează:
  1. oca-gen-addon-readme generează README.rst + index.html (docutils).
  2. Acest script rulează DUPĂ și, pentru fiecare index.html generat de OCA:
       - ȘTERGE titlul docutils + heading-ul-secțiune duplicat (= numele modulului);
       - elimină badge-urile shields, secțiunea RO și TOC-ul local;
       - inserează un HERO inline (verde solid) construit din __manifest__.py;
       - ÎNVELEȘTE tot conținutul rămas într-un PANOU solid (off-white, ink explicit);
       - stilizează heading-urile (bară-accent verde), listele de funcții (carduri),
         chip-urile de cod și paragraful lead;
       - adaugă un bloc de suport + footer Terrabit (inline) la final.
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

TB_MARKER = "<!-- tb-skin v4 -->"
# orice marcaj tb-skin (v1, v2, v3, …) — ca să nu re-îmbrăcăm un fișier deja procesat
ANY_TB_MARKER = re.compile(r"<!-- tb-skin v\d+ -->")

# ---- Paletă & branding (modifică aici o singură dată pentru toate modulele) ----
# Nuanțele oficiale din logo-ul Terrabit: #006F42 verde închis, #57B952 verde deschis.
TB = {
    "primary": "#006F42",  # verde închis (brand) — DOAR pe fundal solid/border
    "dark": "#00432a",  # verde foarte închis (hero pill / bloc suport)
    "accent": "#57B952",  # verde deschis (brand) — bare-accent, bife
    # borduri/separatoare semi-transparente: vizibile ȘI pe light ȘI pe dark
    "line": "rgba(127,160,140,0.40)",
    "line_soft": "rgba(127,160,140,0.22)",
    "website": "https://www.terrabit.ro",
    "company": "Terrabit Solutions SRL",
    # Logo opțional găzduit absolut (Odoo elimină SVG inline). Dacă e gol, footer-ul
    # folosește un wordmark text alb pe blocul verde (mereu funcționează).
    "logo_url": "",
}

FONT = "'Segoe UI','Avenir Next','Helvetica Neue',Arial,sans-serif"

# ----------------------------------------------------------------------------- #
# Fragmente HTML — TOATE stilurile sunt inline ca să reziste la sanitizarea Odoo.
# NB: gradient/`background` shorthand sunt tăiate de store → doar `background-color`.
# ----------------------------------------------------------------------------- #

WRAP_OPEN = f'<div style="max-width:1100px;margin:0 auto;padding:0 16px;font-family:{FONT};">'

HERO = """%(marker)s
<div style="background-color:%(primary)s;color:#ffffff;border-radius:20px;
  padding:54px 40px;text-align:center;margin:8px 0 22px;box-shadow:0 18px 40px rgba(0,67,42,0.28);">
  <div style="display:inline-block;background-color:%(dark)s;color:#9be8b6;font-weight:700;
    letter-spacing:1.5px;padding:7px 18px;border-radius:999px;font-size:11px;
    text-transform:uppercase;margin-bottom:20px;">Odoo Partner &nbsp;&bull;&nbsp; Terrabit</div>
  <h1 style="font-size:42px;line-height:1.08;margin:0 0 14px;color:#ffffff;font-weight:800;
    letter-spacing:-0.5px;border:none;">%(name)s</h1>
  %(summary)s
  <div>
    %(badges)s
  </div>
</div>
"""

SUMMARY = '<p style="font-size:19px;color:#cdeccf;max-width:620px;margin:0 auto 24px;line-height:1.5;">%s</p>'

BADGE = (
    '<span style="display:inline-block;background-color:%(dark)s;color:#ffffff;'
    'padding:8px 16px;border-radius:999px;font-size:12px;font-weight:600;margin:4px;">%(t)s</span>'
)
BADGE_ACCENT = (
    '<span style="display:inline-block;background-color:%(accent)s;color:#04331f;'
    'padding:8px 16px;border-radius:999px;font-size:12px;font-weight:700;margin:4px;">%(t)s</span>'
)

# Container de conținut: TRANSPARENT (fără background/color) -> textul moștenește tema.
# Doar lățime/spațiere/tipografie. Copiii rămân lizibili pe orice temă „sănătoasă".
PANEL_OPEN = '<div style="padding:6px 6px 2px;font-size:16px;line-height:1.65;">'
PANEL_CLOSE = "</div>"

# Blocul de suport + footer: BRAND solid verde închis (theme-independent), include și
# linia de footer (alb / verde-deschis pe verde închis) -> nu mai există footer separat.
SUPPORT = """
<div style="background-color:%(dark)s;color:#ffffff;border-radius:20px;padding:42px 44px 30px;
  margin:24px 0 16px;text-align:center;">
  <h2 style="color:#ffffff;border:none;margin:0 0 10px;font-size:26px;font-weight:800;letter-spacing:-0.3px;">Need help getting started?</h2>
  <p style="color:#bfe3cc;max-width:600px;margin:0 auto 22px;line-height:1.6;font-size:16px;">
     We are an Odoo partner building apps for the Romanian market (SAGA &amp; WinMentor
     export; Romanian accounting localization in progress). Direct support from the team
     that built the module.</p>
  <a href="%(website)s" style="display:inline-block;background-color:%(accent)s;color:#04331f;
     font-weight:800;text-decoration:none;padding:14px 32px;border-radius:12px;font-size:15px;">Contact Terrabit &rarr;</a>
  <div style="border-top:1px solid rgba(255,255,255,0.18);margin:30px auto 0;padding-top:18px;max-width:760px;">
    %(logo)s
    <div style="color:#bfe3cc;font-size:13px;margin-top:6px;">
      &copy; %(company)s &nbsp;&bull;&nbsp;
      <a href="%(website)s" style="color:#ffffff;text-decoration:none;font-weight:600;">terrabit.ro</a>
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
    return '<div style="font-weight:800;color:#ffffff;font-size:19px;letter-spacing:2px;">TERRABIT</div>'


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
    items.append((BADGE_ACCENT, "Dedicated support"))
    if manifest.get("price"):
        cur = manifest.get("currency", "EUR")
        price = manifest["price"]
        price_txt = f"{price:g}" if isinstance(price, (int, float)) else str(price)
        items.append((BADGE_ACCENT, f"{price_txt} {cur}"))
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


# --- heading-uri docutils: bară-accent verde + ink închis ---------------------- #
def style_headings(html):
    """Stilează heading-urile de secțiune (h1/h2/h3 docutils, fără style) cu o bară-accent
    verde la stânga + ink închis pe panou. h1 puțin mai mare ca h2/h3."""
    sizes = {"h1": 27, "h2": 24, "h3": 19}

    def repl(m):
        tag, inner = m.group(1).lower(), m.group(2)
        # docutils înfășoară heading-urile în <a class="toc-backref"> când există un TOC
        # -> fără asta, ancora rămâne albastră de link pe pagină. Dezvelește-o (păstrează textul).
        inner = re.sub(r"<a\b[^>]*toc-backref[^>]*>(.*?)</a>", r"\1", inner, flags=re.I | re.S)
        size = sizes.get(tag, 22)
        # FĂRĂ `color` -> moștenește tema. Identitatea verde vine din bara-accent (border).
        style = (
            f"border:none;border-left:4px solid {TB['accent']};padding-left:16px;"
            f"margin:30px 0 14px;font-size:{size}px;font-weight:800;"
            "letter-spacing:-0.3px;line-height:1.2;"
        )
        return f'<{tag} style="{style}">{inner}</{tag}>'

    return re.sub(r"<(h[1-3])\b[^>]*>(.*?)</\1>", repl, html, flags=re.I | re.S)


def style_code(html):
    """Chip pentru cod inline docutils (<tt class="docutils literal">…</tt>).
    Border + culoare moștenită (fără fundal) -> lizibil pe orice temă."""
    chip = (
        f"border:1px solid {TB['line']};padding:1px 7px;border-radius:6px;"
        "font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;"
    )
    html = re.sub(r'<tt class="docutils literal">(.*?)</tt>', rf'<code style="{chip}">\1</code>', html, flags=re.S)
    return html


def style_lead_paragraph(html):
    """Primul paragraf „gol" (intro) → lead mai mare (culoare moștenită).
    Rulează DUPĂ ce am scos shields/title."""
    return re.sub(
        r"<p>",
        '<p style="font-size:19px;line-height:1.6;margin:0 0 26px;max-width:780px;opacity:0.92;">',
        html,
        count=1,
    )


# --- carduri de funcții (inline) --------------------------------------------- #
UL_GRID = "list-style:none;padding:0;margin:14px 0 30px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px;"
# Carduri ADAPTIVE: fundal transparent + border rgba (vizibil pe ambele teme), text moștenit.
CARD = (
    f"background-color:transparent;border:1px solid {TB['line']};border-radius:14px;"
    "list-style:none;margin:0;line-height:1.5;"
)
CARD_CHECK = CARD + "padding:16px 18px 16px 50px;position:relative;"
CARD_DEF = CARD + "padding:16px 18px;"
BADGE_TICK = (
    f"position:absolute;left:16px;top:17px;width:22px;height:22px;border-radius:7px;"
    f"background-color:{TB['accent']};color:#04331f;font-weight:800;font-size:13px;"
    "text-align:center;line-height:22px;display:inline-block;"
)
# Lead de definiție: BOLD + culoare moștenită (NU verde — ar fi invizibil pe dark / slab pe alb).
DEF_LEAD = "font-weight:800;"
SUB_UL = "list-style:disc;margin:8px 0 0;padding-left:20px;"
SUB_LI = "margin:3px 0;font-size:14px;list-style:disc;opacity:0.9;"


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
    content = re.sub(r"<ul\b[^>]*>", f'<ul style="{SUB_UL}">', content)
    content = re.sub(r"<li\b[^>]*>", f'<li style="{SUB_LI}">', content)
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
                f'<li style="{CARD_DEF}"><span style="{DEF_LEAD}">{lead}</span>'
                f'<div style="margin-top:4px;">{rest}</div></li>'
            )
        else:
            content = _style_sublists(raw)
            parts.append(f'<li style="{CARD_CHECK}"><span style="{BADGE_TICK}">&#10003;</span>{content}</li>')
    return "".join(parts)


def style_feature_lists(html):
    """Transformă listele `ul.simple` (≥3 itemi de nivel superior) în carduri inline.
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
        new_block = f'<ul style="{UL_GRID}">{_render_cards(inner, top)}</ul>'
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

    # 1) curăță: shields, titlu docutils, heading duplicat (= numele), RO, TOC
    html = strip_shields(html)
    html = remove_docutils_title(html)
    html = remove_duplicate_name_heading(html, name)
    html = remove_secondary_language(html)
    html = strip_toc(html)
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
