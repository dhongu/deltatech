#!/usr/bin/env python3
"""
tb_skin_index.py — îmbracă în stil Terrabit fișierele static/description/index.html
generate de oca-gen-addon-readme, FĂRĂ a modifica description.md sau template-ul .jinja.

IMPORTANT (de ce v2 folosește STILURI INLINE):
  Odoo Apps Store NU randează index.html ca atare — îl trece printr-un sanitizer care:
    - ȘTERGE tag-urile <style> (deci orice CSS dintr-un bloc <style> dispare);
    - ȘTERGE wrapper-ul <div class="document"> (deci selectoarele .document … nu mai
      potrivesc nimic);
    - ȘTERGE <svg> inline (deci un logo SVG inline dispare).
  Verificat pe pagina live a unui modul Terrabit deja publicat: hero-ul lipsea,
  CSS-ul nu se aplica, iar titlul apărea de mai multe ori (pentru că ascunderea lui
  se făcea prin CSS, care fusese eliminat).

  Concluzie: tot ce trebuie să se vadă pe store trebuie pus ca `style="..."` INLINE,
  pe fiecare element (exact ce fac Webkul/Emipro). Acest script construiește hero-ul,
  cardurile de funcții și blocul de suport/footer cu stiluri inline.

Cum funcționează:
  1. oca-gen-addon-readme generează README.rst + index.html (docutils).
  2. Acest script rulează DUPĂ și, pentru fiecare index.html generat de OCA:
       - ȘTERGE efectiv (din DOM, nu prin CSS) titlul docutils duplicat;
       - inserează un hero inline construit din __manifest__.py (nume + summary + versiune);
       - transformă listele de funcții (flat) în carduri cu stiluri inline;
       - elimină secțiunea în limba secundară (RO) și TOC-ul local docutils;
       - adaugă un bloc de suport + footer Terrabit (inline) la final.
  3. Atinge DOAR fișierele generate de OCA (care conțin marcajul "oca-gen-addon-readme").

Idempotent: dacă fișierul a fost deja îmbrăcat (conține marcaj tb-skin), îl sare.

Utilizare:
    python tb_skin_index.py --addons-dir .          # tot repo-ul
    python tb_skin_index.py --addon-dir deltatech_delivery_fc
"""

import argparse
import ast
import os
import re

TB_MARKER = "<!-- tb-skin v2 -->"
# orice marcaj tb-skin (v1, v2, …) — ca să nu re-îmbrăcăm un fișier deja procesat
ANY_TB_MARKER = re.compile(r"<!-- tb-skin v\d+ -->")

# ---- Paletă & branding (modifică aici o singură dată pentru toate modulele) ----
# Nuanțele oficiale din logo-ul Terrabit: #006F42 verde închis, #57B952 verde deschis.
TB = {
    "primary": "#006F42",  # verde închis (brand)
    "dark": "#00432a",  # verde foarte închis (start gradient hero / bloc suport)
    "accent": "#57B952",  # verde deschis (brand)
    "ink": "#1f2937",
    "muted": "#64748b",
    "border": "#dbe7df",
    "website": "https://www.terrabit.ro",
    "company": "Terrabit Solutions SRL",
    # Logo opțional găzduit absolut (Odoo elimină SVG inline). Dacă e gol, footer-ul
    # folosește un wordmark text în verde de brand (mereu funcționează).
    "logo_url": "",
}

# ----------------------------------------------------------------------------- #
# Fragmente HTML — TOATE stilurile sunt inline ca să reziste la sanitizarea Odoo.
# ----------------------------------------------------------------------------- #

# NB: Odoo Apps Store taie `background`/`linear-gradient` din style inline; supraviețuiește
# DOAR `background-color` (culoare solidă). De aceea hero-ul e verde solid, fără gradient.
HERO = """%(marker)s
<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
  background-color:%(primary)s;color:#ffffff;
  border-radius:16px;padding:46px 36px;text-align:center;margin:8px auto 32px;max-width:1080px;">
  <div style="display:inline-block;background-color:%(dark)s;color:#ffffff;
    font-weight:700;letter-spacing:0.5px;padding:6px 16px;border-radius:999px;
    font-size:11px;text-transform:uppercase;margin-bottom:16px;">Odoo Partner &bull; Terrabit</div>
  <h1 style="font-size:34px;line-height:1.15;margin:0 0 12px;color:#ffffff;font-weight:800;border:none;">%(name)s</h1>
  %(summary)s
  <div style="margin-top:6px;">
    %(badges)s
  </div>
</div>
"""

BADGE = (
    f'<span style="display:inline-block;background-color:{TB["dark"]};color:#ffffff;'
    'padding:6px 14px;border-radius:999px;font-size:12px;font-weight:600;margin:3px;">%s</span>'
)

SUMMARY = '<p style="font-size:17px;color:#d6ebdd;max-width:680px;margin:0 auto 18px;line-height:1.55;">%s</p>'

SUPPORT = """
<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
  background-color:%(dark)s;color:#ffffff;border-radius:16px;padding:34px;margin:40px auto 16px;max-width:1080px;">
  <h2 style="color:#ffffff;border:none;margin:0 0 8px;font-size:22px;">Need help?</h2>
  <p style="color:#cfe6d8;max-width:640px;margin:0 0 18px;line-height:1.55;">
     We are an Odoo partner building apps for the Romanian market
     (SAGA &amp; WinMentor export; Romanian accounting localization in progress).
     Direct support from the team that built the module.</p>
  <a href="%(website)s" style="display:inline-block;background-color:#ffffff;color:%(dark)s;
     font-weight:700;text-decoration:none;padding:12px 26px;border-radius:10px;">Contact Terrabit</a>
</div>
<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
  text-align:center;color:%(muted)s;font-size:13px;padding:20px 0 8px;max-width:1080px;margin:0 auto;">
  %(logo)s
  &copy; %(company)s &bull;
  <a href="%(website)s" style="color:%(primary)s;">terrabit.ro</a>
  &bull; Odoo apps for Romania, Ireland &amp; Moldova
</div>
"""


def logo_html():
    """Logo footer: <img> absolut dacă e configurat, altfel wordmark text (Odoo taie SVG)."""
    if TB["logo_url"]:
        return (
            f'<div style="margin-bottom:10px;"><img src="{TB["logo_url"]}" alt="{TB["company"]}" '
            'style="height:40px;width:auto;border:none;"/></div>'
        )
    return (
        f'<div style="font-weight:800;color:{TB["primary"]};font-size:18px;'
        'letter-spacing:1px;margin-bottom:6px;">TERRABIT</div>'
    )


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
        items.append(f"Odoo {m.group(1)}")
    items += ["Online &bull; Odoo.sh &bull; On-premise", "Dedicated support"]
    if manifest.get("price"):
        cur = manifest.get("currency", "EUR")
        price = manifest["price"]
        price_txt = f"{price:g}" if isinstance(price, (int, float)) else str(price)
        items.append(f"{price_txt} {cur}")
    return "\n    ".join(BADGE % b for b in items)


# Texte de heading care marchează secțiunea în limba secundară (fără diacritice, lowercase).
RO_MARKERS = ("romana", "romaneste", "limba romana", "descriere ro", "versiune in romana")


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


def remove_docutils_title(html):
    """Șterge EFECTIV titlul/subtitlul docutils duplicat (nu prin CSS — care ar fi eliminat
    de Odoo, lăsând titlul vizibil de mai multe ori). Preluăm titlul în hero."""
    html = re.sub(r'<h1 class="title">.*?</h1>\s*', "", html, count=1, flags=re.S)
    html = re.sub(r'<p class="subtitle">.*?</p>\s*', "", html, count=1, flags=re.S)
    return html


def strip_toc(html):
    """Elimină TOC-ul local docutils („Table of contents" + lista) — redundant pe o pagină
    de prezentare."""
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


# --- carduri de funcții (inline) --------------------------------------------- #
UL_GRID = "list-style:none;padding:0;margin:14px 0;display:grid;grid-template-columns:repeat(2,1fr);gap:12px;"
LI_CARD = (
    f"background-color:#ffffff;border:1px solid {TB['border']};border-radius:12px;"
    "padding:14px 16px 14px 42px;position:relative;list-style:none;margin:0;"
)
LI_DOT = (
    "position:absolute;left:14px;top:17px;width:14px;height:14px;border-radius:4px;"
    f"display:inline-block;background-color:{TB['accent']};"
)
# sub-listele dintr-un card (docutils le emite ca <ul> simplu, fără class)
SUB_UL = "list-style:disc;margin:10px 0 0;padding-left:20px;"
SUB_LI = "margin:3px 0;color:#475569;font-size:14px;list-style:disc;"


def _ul_end(html, start):
    """Sfârșitul (exclusiv) blocului <ul ...> care începe la `start`, prin numărarea <ul>/<ul>."""
    depth = 0
    for m in re.finditer(r"<ul\b|</ul>", html[start:]):
        depth += 1 if m.group(0) != "</ul>" else -1
        if depth == 0:
            return start + m.end()
    return None


def _split_top_li(inner):
    """Spans (start, end) ale <li>...</li> de nivel superior din conținutul unui <ul>,
    respectând sub-listele <ul> imbricate."""
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
    """Stilează sub-listele dintr-un card (inline): <ul> simplu + <li> ca buline mici."""
    content = re.sub(r"<ul\b[^>]*>", f'<ul style="{SUB_UL}">', content)
    content = re.sub(r"<li\b[^>]*>", f'<li style="{SUB_LI}">', content)
    return content


def _render_cards(inner, top):
    parts = []
    for s, e in top:
        cm = re.match(r"<li\b[^>]*>(.*)</li>\s*$", inner[s:e], re.S)
        content = _style_sublists(cm.group(1) if cm else inner[s:e])
        parts.append(f'<li style="{LI_CARD}"><span style="{LI_DOT}"></span>{content}</li>')
    return "".join(parts)


def style_feature_lists(html):
    """Transformă listele de funcții `ul.simple` (≥3 itemi de nivel superior) în carduri
    cu stiluri inline. Tratează ȘI listele cu sub-liste (titlu bold + sub-puncte în card),
    nu doar pe cele plate. Listele scurte (Authors/Maintainers, Limitations) rămân plate.
    Docutils marchează lista exterioară cu `class="simple"` și sub-listele ca `<ul>` simplu."""
    repls = []
    for m in re.finditer(r'<ul class="simple">', html):
        end = _ul_end(html, m.start())
        if end is None:
            continue
        inner = html[m.end() : end - len("</ul>")]
        top = _split_top_li(inner)
        if len(top) < 3:  # listă scurtă -> o lăsăm plată
            continue
        new_block = f'<ul style="{UL_GRID}">{_render_cards(inner, top)}</ul>'
        repls.append((m.start(), end, new_block))
    for s, e, nb in reversed(repls):  # în ordine inversă, ca indicii să rămână valizi
        html = html[:s] + nb + html[e:]
    return html


def skin_html(html, manifest):
    if ANY_TB_MARKER.search(html):
        return None  # deja procesat
    if "oca-gen-addon-readme" not in html:
        return None  # index.html scris manual -> nu atingem

    name = manifest.get("name") or ""
    summary = manifest.get("summary") or ""
    hero = HERO % {
        "marker": TB_MARKER,
        "name": name,
        "summary": (SUMMARY % summary) if summary else "",
        "badges": build_badges(manifest),
        **TB,
    }
    support = SUPPORT % dict(TB, logo=logo_html())

    # 1) șterge titlul docutils duplicat (din DOM)
    html = remove_docutils_title(html)
    # 2) elimină secțiunea RO și TOC-ul local
    html = remove_secondary_language(html)
    html = strip_toc(html)
    # 3) carduri de funcții (inline)
    html = style_feature_lists(html)
    # 4) injectează hero imediat după <div class="document"...> (sau după <body>)
    if re.search(r'<div class="document"[^>]*>', html):
        html = re.sub(r'<div class="document"[^>]*>', lambda m: m.group(0) + hero, html, count=1)
    else:
        html = re.sub(r"<body[^>]*>", lambda m: m.group(0) + hero, html, count=1)
    # 5) adaugă blocul de suport + footer înainte de </div>-ul .document (sau </body>)
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
