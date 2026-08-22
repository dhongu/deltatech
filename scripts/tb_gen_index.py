#!/usr/bin/env python3
"""
tb_gen_index.py — generează static/description/index.html DIRECT din fragmentele
readme/*.md + __manifest__.py, în stil Terrabit (v1, succesorul lui tb_skin_index.py).

De ce generare directă (nu skin peste docutils):
  tb_skin_index.py (v1–v5) post-procesa cu regex HTML-ul produs de oca-gen-addon-readme —
  fragil (TOC, shields, heading duplicat, secțiune RO…). Aici controlăm HTML-ul de la
  sursă: citim readme/DESCRIPTION.md, CONFIGURE.md, USAGE.md, HISTORY.md (+ INSTALL.md,
  CONTEXT.md), le randăm cu python-markdown și le așezăm în structura noastră.
  README.rst rămâne în continuare treaba lui oca-gen-addon-readme — nu ne atingem de el.

Reguli sanitizer Apps Store (moștenite din tb_skin_index v5, validate pe store real):
  - ȘTERGE <style> și <script>       → doar clase Bootstrap + stiluri inline;
  - ȘTERGE <svg> inline              → logo doar <img> sau wordmark text;
  - TAIE `background:`/gradient      → supraviețuiește DOAR `background-color` solid;
  - PĂSTREAZĂ `class` și `data-bs-*` → clasele Bootstrap 5 sunt stilizate de bundle-ul
    frontend al store-ului, iar componentele declarative (nav-pills cu data-bs-toggle)
    sunt activate de bootstrap.bundle.js al store-ului — fără JS propriu.
    (Confirmat pe module live, ex. bom_excel_import / NextERP.)

Structura paginii (doar EN):
  HERO verde brand (icon.png + nume + summary + badge-uri din manifest)
  NAV-PILLS cu taburi: Overview / Configuration / Usage / Versions
    - Overview      = DESCRIPTION.md (+ CONTEXT.md la final); listele de funcții cu
                      ≥3 itemi devin carduri Bootstrap cu bifă verde
    - Configuration = INSTALL.md + CONFIGURE.md
    - Usage         = USAGE.md
    - Versions      = HISTORY.md (limitat la ultimele MAX_HISTORY_VERSIONS versiuni)
    (taburile fără fragment sursă nu apar; cu un singur tab, nav-ul se omite)
  STATS Terrabit (3 carduri) + bloc suport/CTA (mereu vizibile, sub taburi)
  CROSS-SELL „More apps by Terrabit" — carduri către module-surori din aceeași suită
    (aceeași categorie întâi, alfabetic), link spre apps.odoo.com

Textul NU primește `color` → moștenește tema Bootstrap (lizibil pe light ȘI dark).
Verdele Terrabit DOAR ca `background-color`/bordură, niciodată singura sursă de
lizibilitate. Validare: scripts/tb_apps_preview.py (light + dark-sane).

Ieșirea e un FRAGMENT de body (fără <html>/<head>) — store-ul oricum despachetează,
iar tb_apps_preview.py îl îmbracă în shell-ul lui.

Suprascriere: scrie peste index.html DOAR dacă lipsește sau poartă un marcaj de
generator cunoscut (oca-gen-addon-readme / tb-skin / tb-gen). Un index.html scris
de mână e sărit (folosește --force ca să-l înlocuiești).

Utilizare:
    python3 tb_gen_index.py --addon-dir deltatech_delivery_status
    python3 tb_gen_index.py --addons-dir .            # toată suita
    python3 tb_gen_index.py --addon-dir X --no-cross-sell
"""

import argparse
import ast
import html as html_mod
import os
import re

import markdown

TB_MARKER = "<!-- tb-gen v1 -->"
KNOWN_MARKERS = ("oca-gen-addon-readme", "tb-skin v", "tb-gen v")

MAX_HISTORY_VERSIONS = 10
CROSS_SELL_COUNT = 8

# ---- Paletă & branding (un singur loc pentru toate modulele) ----
# Nuanțele oficiale din logo-ul Terrabit: #006F42 verde închis, #57B952 verde deschis.
TB = {
    "primary": "#006F42",
    "dark": "#00432a",
    "accent": "#57B952",
    "website": "https://www.terrabit.ro",
    "contact_url": "https://www.terrabit.ro/contactus",
    "company": "Terrabit Solutions SRL",
    "apps_author": "Terrabit",  # filtru author pe apps.odoo.com
}

FONT = "'Segoe UI','Avenir Next','Helvetica Neue',Arial,sans-serif"

MD_EXTENSIONS = ["tables", "fenced_code", "sane_lists"]

# Fragmentele readme → taburi (ordinea = ordinea taburilor)
TABS = [
    ("overview", "Overview", ("DESCRIPTION.md", "CONTEXT.md")),
    ("configure", "Configuration", ("INSTALL.md", "CONFIGURE.md")),
    ("usage", "Usage", ("USAGE.md",)),
    ("versions", "Versions", ("HISTORY.md",)),
]

# ----------------------------------------------------------------------------- #
# Fragmente HTML — LAYOUT/TEMĂ prin clase Bootstrap; brand-ul verde prin
# `background-color` inline (singurul care supraviețuiește sanitizarea).
# ----------------------------------------------------------------------------- #

WRAP_OPEN = f'<div class="mx-auto px-3" style="max-width:1100px;font-family:{FONT};">'

HERO = """%(marker)s
<div class="text-white text-center rounded-4 shadow px-4 py-5 mt-2 mb-4" style="background-color:%(primary)s;">
  <span class="d-inline-block rounded-pill fw-bold text-uppercase mb-4"
    style="background-color:%(dark)s;color:#9be8b6;letter-spacing:1.5px;padding:7px 18px;font-size:11px;">Odoo Partner &nbsp;&bull;&nbsp; Terrabit</span>
  %(icon)s
  <h1 class="text-white fw-bold mb-3" style="font-size:42px;line-height:1.08;letter-spacing:-0.5px;border:none;">%(name)s</h1>
  %(summary)s
  <div>
    %(badges)s
  </div>
</div>
"""

HERO_ICON = (
    '<div class="mb-3"><span class="d-inline-block rounded-3 p-2" style="background-color:#ffffff;">'
    '<img src="icon.png" alt="%(name)s" style="width:72px;height:72px;border:none;"/></span></div>'
)

SUMMARY = '<p class="mx-auto mb-4" style="font-size:19px;color:#cdeccf;max-width:620px;line-height:1.5;">%s</p>'

BADGE = (
    '<span class="d-inline-block rounded-pill fw-semibold text-white m-1"'
    ' style="background-color:%(dark)s;padding:8px 16px;font-size:12px;">%(t)s</span>'
)
BADGE_ACCENT = (
    '<span class="d-inline-block rounded-pill fw-bold m-1"'
    ' style="background-color:%(accent)s;color:#04331f;padding:8px 16px;font-size:12px;">%(t)s</span>'
)

# Nav-pills: fără JS propriu — data-bs-toggle e activat de bootstrap.bundle.js al store-ului.
# pilula activă în verde Terrabit prin variabila CSS Bootstrap (inline, deci trece de
# sanitizer în emulator; dacă store-ul o taie totuși, fallback = albastrul BS implicit)
NAV_OPEN = (
    '<ul class="nav nav-pills justify-content-center mb-4 pb-3 border-bottom"'
    f' style="--bs-nav-pills-link-active-bg:{TB["primary"]};">'
)
NAV_ITEM = """  <li class="nav-item mx-1 mb-2">
    <a class="nav-link%(active)s fw-semibold rounded-pill border" id="tb-tab-%(key)s"
       data-bs-toggle="pill" data-bs-target="#tb-panel-%(key)s" href="#tb-panel-%(key)s"
       style="padding:10px 22px;">%(title)s</a>
  </li>"""
NAV_CLOSE = "</ul>"

# Panou: `text-body` (theme-aware) dă culoarea corpului pe orice temă gazdă.
PANEL = """<div class="tab-pane fade%(active)s py-2 text-body" id="tb-panel-%(key)s" style="font-size:16px;line-height:1.65;">
%(heading)s
%(body)s
</div>"""

# Stats + bloc suport: BRAND solid verde închis (theme-independent).
STATS = """
<div class="row text-center mt-4 mb-1 g-3">
  %(cards)s
</div>
"""
STAT_CARD = """<div class="col-md-%(col)s">
    <div class="border rounded-3 p-4 h-100">
      <div class="fw-bold" style="font-size:2.2rem;color:%(primary)s;line-height:1;">%(big)s</div>
      <div class="text-body-secondary mt-2" style="font-size:0.9rem;">%(small)s</div>
    </div>
  </div>"""
STAT_ITEMS = [
    ("350+", "Modules published on Odoo Apps"),
    ("Silver", "Odoo Partner &mdash; implementation &amp; support"),
]

SUPPORT = """
<div class="text-white text-center rounded-4 px-4 pt-5 pb-4 mt-4 mb-3" style="background-color:%(dark)s;">
  <h2 class="text-white fw-bold mb-2" style="font-size:26px;letter-spacing:-0.3px;border:none;">Need help getting started?</h2>
  <p class="mx-auto mb-4" style="color:#bfe3cc;max-width:660px;line-height:1.6;font-size:16px;">
     Our 350+ apps on the Odoo Apps Store are used in Odoo implementations across Europe,
     the Americas, Asia and Africa &mdash; by companies we have never even met. That is the
     advantage of building modules that simply work.</p>
  <a href="%(contact_url)s" target="_blank" rel="noopener"
     class="d-inline-block fw-bold text-decoration-none rounded-3"
     style="background-color:%(accent)s;color:#04331f;padding:14px 32px;font-size:15px;">Contact Terrabit &rarr;</a>
</div>
"""

CROSS_SELL_OPEN = """
<section class="rounded-4 p-4 mb-3 border">
  <h2 class="text-center fw-bold mb-1" style="font-size:24px;border:none;">More apps by Terrabit</h2>
  <p class="text-center text-body-secondary mb-4">Other modules from the same publisher, built to work together.
    <a href="https://apps.odoo.com/apps/browse?author=%(apps_author)s" target="_blank" rel="noopener"
       class="fw-semibold" style="color:%(primary)s;">All apps &rarr;</a></p>
  <div class="row g-3">
"""
CROSS_SELL_CARD = """    <div class="col-md-3 col-sm-6">
      <a href="https://apps.odoo.com/apps/modules/%(series)s/%(tech)s" target="_blank" rel="noopener"
         class="card h-100 text-decoration-none border text-body">
        <div class="card-body p-3">
          <div class="d-flex align-items-center mb-2">
            <span class="d-inline-block text-center text-white fw-bold rounded me-2 flex-shrink-0"
                  style="width:40px;height:40px;line-height:40px;font-size:14px;background-color:%(primary)s;">%(initials)s</span>
            <span>
              <span class="d-block fw-semibold" style="font-size:14px;line-height:1.2;">%(name)s</span>
              <span class="d-block text-body-secondary" style="font-size:11px;">%(category)s</span>
            </span>
          </div>
          <p class="text-body-secondary mb-0" style="font-size:12px;">%(summary)s</p>
        </div>
      </a>
    </div>
"""
CROSS_SELL_CLOSE = "  </div>\n</section>\n"

# --- carduri de funcții (grilă Bootstrap responsivă), moștenite din tb_skin_index v5 --- #
UL_GRID = "list-unstyled row row-cols-1 row-cols-md-2 g-3 mt-1 mb-4"
CARD = "border rounded-3 p-3 h-100"
BADGE_TICK = "flex-shrink-0 text-center fw-bold rounded d-inline-block"
BADGE_TICK_STYLE = (
    f"background-color:{TB['accent']};color:#04331f;width:22px;height:22px;line-height:22px;font-size:13px;"
)
SUB_UL = "ps-3 mt-2"
SUB_LI = "small"


# ----------------------------------------------------------------------------- #
# Citire surse
# ----------------------------------------------------------------------------- #


def read_manifest(addon_dir):
    for fn in ("__manifest__.py", "__openerp__.py"):
        path = os.path.join(addon_dir, fn)
        if os.path.exists(path):
            with open(path, encoding="utf8") as f:
                return ast.literal_eval(f.read())
    return {}


def read_fragment(addon_dir, filename):
    path = os.path.join(addon_dir, "readme", filename)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf8") as f:
        return f.read().strip()


def _norm(text):
    table = str.maketrans("ăâîșşțţ", "aaisstt")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text)).translate(table).lower().strip()


GENERIC_LEAD_HEADINGS = {"description", "overview", "descriere"}


def strip_title_heading(md_text, name):
    """Scoate heading-ul de deschidere din DESCRIPTION.md dacă repetă numele modulului
    (apare deja în hero) sau e generic („Description"/„Overview" — redundant sub titlul
    tabului Overview). Acoperă și forma setext (text subliniat cu --- / ===)."""
    m = re.match(r"\s*#{1,3}\s+(.+?)\s*\n", md_text) or re.match(r"\s*(\S[^\n]*?)\s*\n[-=]{3,}\s*\n", md_text)
    if m:
        text = _norm(m.group(1))
        if text == _norm(name) or text in GENERIC_LEAD_HEADINGS:
            return md_text[m.end() :].lstrip("\n")
    return md_text


def cap_history(md_text, max_versions=MAX_HISTORY_VERSIONS):
    """Păstrează doar primele `max_versions` secțiuni de versiune (## X.Y.Z...)."""
    headings = [m.start() for m in re.finditer(r"(?m)^##\s", md_text)]
    if len(headings) <= max_versions:
        return md_text
    kept = md_text[: headings[max_versions]].rstrip()
    return kept + "\n\n*Older releases are listed in the module's HISTORY file.*\n"


# ----------------------------------------------------------------------------- #
# Stilizare HTML randat din Markdown
# ----------------------------------------------------------------------------- #


def style_headings(rendered):
    """Heading-uri cu bară-accent verde la stânga; FĂRĂ `color` -> moștenește tema."""
    sizes = {"h1": 24, "h2": 24, "h3": 19, "h4": 17}

    def repl(m):
        tag, inner = m.group(1).lower(), m.group(2)
        size = sizes.get(tag, 17)
        style = (
            f"border:none;border-left:4px solid {TB['accent']};padding-left:16px;"
            f"font-size:{size}px;letter-spacing:-0.3px;line-height:1.2;"
        )
        return f'<{tag} class="fw-bold mt-4 mb-3" style="{style}">{inner}</{tag}>'

    return re.sub(r"<(h[1-4])\b[^>]*>(.*?)</\1>", repl, rendered, flags=re.I | re.S)


def style_code(rendered):
    """Chip pentru <code> inline + bloc <pre> cu bordură theme-aware."""
    mono = "font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;"
    # blocurile <pre><code> întâi (ca să nu primească și chip-ul inline)
    rendered = re.sub(
        r"<pre\b[^>]*>",
        f'<pre class="border rounded-3 p-3 my-3" style="{mono}font-size:13px;overflow-x:auto;">',
        rendered,
    )
    parts = re.split(r"(<pre\b.*?</pre>)", rendered, flags=re.S)
    for i, part in enumerate(parts):
        if part.startswith("<pre"):
            continue
        parts[i] = re.sub(
            r"<code\b[^>]*>",
            f'<code class="border rounded px-2" style="{mono}font-size:13px;">',
            part,
        )
    return "".join(parts)


def style_tables(rendered):
    """Tabelele Markdown primesc clasele Bootstrap (theme-aware)."""
    return re.sub(r"<table\b[^>]*>", '<table class="table table-bordered" style="font-size:14px;">', rendered)


def style_lead_paragraph(rendered):
    """Primul paragraf al Overview-ului → lead mai mare (culoare moștenită)."""
    return re.sub(
        r"<p>",
        '<p class="mb-4" style="font-size:19px;line-height:1.6;max-width:780px;opacity:0.92;">',
        rendered,
        count=1,
    )


def _ul_end(rendered, start):
    depth = 0
    for m in re.finditer(r"<ul\b|</ul>", rendered[start:]):
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
        # item „definiție": începe cu <strong>lead</strong>: detaliu
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


def style_feature_lists(rendered):
    """Listele de nivel superior cu ≥3 itemi devin carduri Bootstrap (bifă verde /
    card-definiție pentru itemii cu lead bold). Listele scurte rămân plate."""
    repls = []
    pos = 0
    while True:
        m = re.search(r"<ul>", rendered[pos:])
        if not m:
            break
        start = pos + m.start()
        end = _ul_end(rendered, start)
        if end is None:
            break
        inner = rendered[start + len("<ul>") : end - len("</ul>")]
        top = _split_top_li(inner)
        if len(top) >= 3:
            repls.append((start, end, f'<ul class="{UL_GRID}">{_render_cards(inner, top)}</ul>'))
        pos = end
    for s, e, nb in reversed(repls):
        rendered = rendered[:s] + nb + rendered[e:]
    return rendered


def normalize_list_indent(md_text):
    """Readme-urile sunt scrise pentru GitHub (sub-liste la 2 spații), dar python-markdown
    cere 4 — altfel sub-punctele devin itemi de nivel superior (și carduri separate)."""
    return re.sub(r"(?m)^ {2,3}(?=(?:[-*+]|\d+\.) )", "    ", md_text)


def render_markdown(md_text):
    return markdown.markdown(normalize_list_indent(md_text), extensions=MD_EXTENSIONS)


# ----------------------------------------------------------------------------- #
# Construcția paginii
# ----------------------------------------------------------------------------- #


def build_badges(manifest):
    items = []
    ver = str(manifest.get("version", ""))
    m = re.match(r"(\d+\.\d+)", ver)
    if m:
        items.append((BADGE_ACCENT, f"Odoo {m.group(1)}"))
    category = manifest.get("category")
    if category:
        items.append((BADGE, html_mod.escape(str(category))))
    license_ = manifest.get("license")
    if license_:
        items.append((BADGE, html_mod.escape(str(license_))))
    items.append((BADGE, "Online &bull; Odoo.sh &bull; On-premise"))
    return "\n    ".join(tmpl % dict(TB, t=t) for tmpl, t in items)


def build_hero(addon_dir, manifest):
    name = html_mod.escape(manifest.get("name") or os.path.basename(os.path.abspath(addon_dir)))
    summary = html_mod.escape((manifest.get("summary") or "").strip())
    icon = ""
    if os.path.exists(os.path.join(addon_dir, "static", "description", "icon.png")):
        icon = HERO_ICON % {"name": name}
    return HERO % dict(
        TB,
        marker=TB_MARKER,
        icon=icon,
        name=name,
        summary=(SUMMARY % summary) if summary else "",
        badges=build_badges(manifest),
    )


def build_tab_sources(addon_dir, manifest, allow_ro=False):
    """Întoarce [(key, title, markdown)] doar pentru taburile cu fragment existent."""
    name = manifest.get("name") or ""
    tabs = []
    for key, title, files in TABS:
        chunks = [read_fragment(addon_dir, fn) for fn in files]
        md_text = "\n\n".join(c for c in chunks if c)
        if not md_text:
            continue
        if key == "overview":
            md_text = strip_title_heading(md_text, name)
        if key == "versions":
            # pagina e implicit în EN — un HISTORY.md scris în română (diacritice) nu
            # urcă; excepție suitele cu prezentare intenționat RO (--allow-ro, ex.
            # l10n_ro_ent, unde publicul Apps Store e românesc)
            if not allow_ro and re.search(r"[ăâîșşțţĂÂÎȘŞȚŢ]", md_text):
                continue
            md_text = cap_history(md_text)
        tabs.append((key, title, md_text))
    return tabs


def build_panel_body(key, md_text):
    rendered = render_markdown(md_text)
    rendered = style_tables(rendered)
    rendered = style_code(rendered)
    if key == "overview":
        rendered = style_feature_lists(rendered)
        rendered = style_lead_paragraph(rendered)
    rendered = style_headings(rendered)
    return rendered


def build_tabs(tabs):
    if not tabs:
        return ""
    accent_bar = (
        f"border:none;border-left:4px solid {TB['accent']};padding-left:16px;"
        "font-size:24px;letter-spacing:-0.3px;line-height:1.2;"
    )
    panes = []
    for i, (key, title, md_text) in enumerate(tabs):
        heading = f'<h2 class="fw-bold mb-3" style="{accent_bar}">{title}</h2>'
        panes.append(
            PANEL
            % {
                "active": " show active" if i == 0 else "",
                "key": key,
                "heading": heading,
                "body": build_panel_body(key, md_text),
            }
        )
    if len(tabs) == 1:
        return panes[0]
    nav = [NAV_OPEN]
    for i, (key, title, _md) in enumerate(tabs):
        nav.append(NAV_ITEM % {"active": " active" if i == 0 else "", "key": key, "title": title})
    nav.append(NAV_CLOSE)
    return "\n".join(nav) + '\n<div class="tab-content">\n' + "\n".join(panes) + "\n</div>"


def _initials(name):
    words = re.findall(r"[A-Za-z0-9]+", name)
    words = [w for w in words if w.lower() not in ("deltatech", "terrabit")] or words
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    return (words[0][:2] if words else "TB").upper()


def _truncate(text, limit=120):
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


def collect_siblings(addon_dir):
    """Modulele-surori din aceeași suită: aceeași categorie întâi, apoi restul, alfabetic."""
    root = os.path.dirname(os.path.abspath(addon_dir)) or "."
    self_tech = os.path.basename(os.path.abspath(addon_dir))
    self_cat = str(read_manifest(addon_dir).get("category") or "")
    same_cat, others = [], []
    for entry in sorted(os.listdir(root)):
        d = os.path.join(root, entry)
        if entry == self_tech or not os.path.isdir(d):
            continue
        manifest = read_manifest(d)
        if not manifest or manifest.get("installable") is False:
            continue
        item = (entry, manifest)
        (same_cat if str(manifest.get("category") or "") == self_cat else others).append(item)
    return same_cat + others


def build_cross_sell(addon_dir, manifest, count=CROSS_SELL_COUNT):
    ver = str(manifest.get("version", ""))
    m = re.match(r"(\d+\.\d+)", ver)
    series = m.group(1) if m else "19.0"
    cards = []
    for tech, sib in collect_siblings(addon_dir)[:count]:
        cards.append(
            CROSS_SELL_CARD
            % {
                **TB,
                "series": series,
                "tech": tech,
                "initials": _initials(sib.get("name") or tech),
                "name": html_mod.escape(sib.get("name") or tech),
                "category": html_mod.escape(str(sib.get("category") or "")),
                "summary": html_mod.escape(_truncate(sib.get("summary") or sib.get("name") or tech)),
            }
        )
    if not cards:
        return ""
    return (CROSS_SELL_OPEN % TB) + "".join(cards) + CROSS_SELL_CLOSE


def build_stats():
    col = max(3, 12 // max(1, len(STAT_ITEMS)))
    cards = "\n  ".join(STAT_CARD % dict(TB, big=big, small=small, col=col) for big, small in STAT_ITEMS)
    return STATS % {"cards": cards}


def gen_index(addon_dir, cross_sell=True, allow_ro=False):
    manifest = read_manifest(addon_dir)
    tabs = build_tab_sources(addon_dir, manifest, allow_ro=allow_ro)
    parts = [
        WRAP_OPEN,
        build_hero(addon_dir, manifest),
        build_tabs(tabs),
        build_stats(),
        SUPPORT % TB,
        build_cross_sell(addon_dir, manifest) if cross_sell else "",
        "</div>\n",
    ]
    return "\n".join(p for p in parts if p)


# ----------------------------------------------------------------------------- #
# CLI
# ----------------------------------------------------------------------------- #


def may_overwrite(index_path):
    if not os.path.exists(index_path):
        return True
    with open(index_path, encoding="utf8") as f:
        existing = f.read()
    return any(marker in existing for marker in KNOWN_MARKERS)


def process(addon_dir, cross_sell=True, force=False, allow_ro=False):
    if not read_manifest(addon_dir):
        return False
    if not read_fragment(addon_dir, "DESCRIPTION.md"):
        print(f"[tb-gen] SKIP {addon_dir}: fără readme/DESCRIPTION.md")
        return False
    desc_dir = os.path.join(addon_dir, "static", "description")
    index_path = os.path.join(desc_dir, "index.html")
    if not force and not may_overwrite(index_path):
        print(f"[tb-gen] SKIP {index_path}: index.html manual (folosește --force)")
        return False
    # generează ÎNAINTE de a deschide fișierul — o eroare la generare nu trebuie
    # să lase un index.html trunchiat
    content = gen_index(addon_dir, cross_sell=cross_sell, allow_ro=allow_ro)
    os.makedirs(desc_dir, exist_ok=True)
    with open(index_path, "w", encoding="utf8") as f:
        f.write(content)
    print(f"[tb-gen] {index_path}")
    return True


def find_addons(addons_dir):
    for entry in sorted(os.listdir(addons_dir)):
        d = os.path.join(addons_dir, entry)
        if os.path.isdir(d) and (
            os.path.exists(os.path.join(d, "__manifest__.py")) or os.path.exists(os.path.join(d, "__openerp__.py"))
        ):
            yield d


def main():
    ap = argparse.ArgumentParser(description="Generator index.html Apps Store (stil Terrabit) din readme/*.md")
    ap.add_argument("--addon-dir", action="append", default=[], help="un singur modul")
    ap.add_argument("--addons-dir", help="director cu mai multe module")
    ap.add_argument("--no-cross-sell", action="store_true", help="fără secțiunea de module-surori")
    ap.add_argument("--force", action="store_true", help="suprascrie și index.html scrise manual")
    ap.add_argument(
        "--allow-ro", action="store_true", help="suită cu prezentare în RO (nu omite HISTORY cu diacritice)"
    )
    args = ap.parse_args()

    targets = list(args.addon_dir)
    if args.addons_dir:
        targets += list(find_addons(args.addons_dir))
    if not targets:
        targets = list(find_addons("."))

    count = sum(
        1 for d in targets if process(d, cross_sell=not args.no_cross_sell, force=args.force, allow_ro=args.allow_ro)
    )
    print(f"[tb-gen] gata: {count} module generate.")


if __name__ == "__main__":
    main()
