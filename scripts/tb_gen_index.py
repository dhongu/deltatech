#!/usr/bin/env python3
"""
tb_gen_index.py — generează static/description/index.html DIRECT din fragmentele
readme/*.md + __manifest__.py, în stil Terrabit (v1, succesorul lui tb_skin_index.py).

SURSA CANONICĂ: odoo-addons/bitshop/scripts/tb_gen_index.py. Celelalte suite țin o copie
identică (pre-commit-ul fiecărei suite are nevoie de ea local), sincronizată cu
`python3 bitshop/scripts/tb_sync_gen_index.py` rulat din odoo-addons/. Nu edita copiile
din alte suite: diferențele dintre suite sunt opțiuni de linie de comandă, puse în
.pre-commit-config.yaml-ul suitei (--allow-ro, --lang, --scope-note).

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
  NAV-PILLS cu taburi: Overview / Presentation / Configuration / Usage / Română / Versions
    - Overview      = DESCRIPTION.md (+ CONTEXT.md la final); listele de funcții cu
                      ≥3 itemi devin carduri Bootstrap cu bifă verde. Dacă modulul
                      depinde (oricât de indirect, în aceeași suită) de un modul cu
                      readme/FRAMEWORK_FEATURES.md, fragmentul acela se anexează aici
                      (ex. capacitățile comune ale conectoarelor deltatech_marketplace)
    - Presentation  = PRESENTATION.md (opțional): slide-uri exportate ca imagini în
                      static/description/, cu căile relative la index.html
                      (generate de scripts/tb_slides_render.py)
    - Configuration = INSTALL.md + CONFIGURE.md
    - Usage         = USAGE.md
    - Română        = DESCRIPTION.ro.md + CONFIGURE.ro.md + USAGE.ro.md (doar la modulele RO)
    - Versions      = HISTORY.md (limitat la ultimele MAX_HISTORY_VERSIONS versiuni)
    (taburile fără fragment sursă nu apar; cu un singur tab, nav-ul se omite)
  STATS Terrabit (3 carduri) + nota de acoperire a pretului (doar cu --scope-note)
  + bloc suport/CTA (mereu vizibile, sub taburi)
  CROSS-SELL „More apps by Terrabit" — carduri către module-surori din aceeași suită
    (aceeași categorie întâi, alfabetic), link spre apps.odoo.com

Textul primește `color` explicit (TB["body"] / TB["muted"]): store-ul Odoo Apps
randează descrierea pe fundal alb, iar culoarea moștenită de acolo ieșea gri-deschis
și greu lizibilă. Ambele nuanțe sunt alese pentru fundal deschis, iar wrapper-ul își
impune propriul `background-color:#ffffff` + reset de variabile Bootstrap (THEME_RESET):
în backendul Odoo aceeași descriere e randată în tema curentă, iar pe tema dark fundalul
moștenit e închis — fără fundal propriu, textul închis devine invizibil.
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
    python3 tb_gen_index.py --addons-dir . --allow-ro --scope-note   # l10n_ro_ent
"""

import argparse
import ast
import html as html_mod
import logging
import os
import re
import sys

import markdown

_logger = logging.getLogger(__name__)

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
    # Apps Store: în descriere sunt permise doar linkuri mailto:, YouTube și resurse din
    # static/description/ — orice alt link extern e invalidat (vendor guidelines).
    "contact_url": "mailto:support@terrabit.ro",
    "company": "Terrabit Solutions SRL",
    "apps_author": "Terrabit",  # filtru author pe apps.odoo.com
    "body": "#212529",  # culoarea de corp, vezi BODY/MUTED mai jos
    "muted": "#3d4752",  # gri-inchis: ~9.5:1 pe alb, lizibil si la 11-12px
}

FONT = "'Segoe UI','Avenir Next','Helvetica Neue',Arial,sans-serif"

MD_EXTENSIONS = ["tables", "fenced_code", "sane_lists"]

# Capacități comune unei familii de module (ex. toate conectoarele marketplace: async prin
# queue_job, starea de sincronizare, Update Price Only...), scrise o singură dată în
# readme/FRAMEWORK_FEATURES.md al modulului de bază și anexate automat la Overview-ul
# oricărui modul care depinde de el — inclusiv la el însuși. Înainte, doar Shopify le
# documenta, de mână, și rămăsese deja o versiune în urmă până a apucat să iasă pe store.
FRAMEWORK_FRAGMENT = "FRAMEWORK_FEATURES.md"

# ----------------------------------------------------------------------------- #
# Stringurile vizibile ale paginii, pe limbi
#
# Conținutul taburilor vine din `readme/*.md` și are limba suitei; ce e generat aici
# (etichete de tab, stats, note, CTA) are nevoie de o limbă explicită, altfel pagina
# iese amestecată — corp românesc în ramă englezească. `--lang ro` e pentru suitele de
# localizare, unde publicul de pe Apps Store e românesc; restul suitelor rămân pe EN.
# ----------------------------------------------------------------------------- #

I18N = {
    "en": {
        "tab_overview": "Overview",
        "tab_presentation": "Presentation",
        "tab_configure": "Configuration",
        "tab_usage": "Usage",
        "tab_versions": "Versions",
        "tab_romana": "Română",
        "stat_modules": "Modules published on Odoo Apps",
        "stat_partner": "Odoo Partner &mdash; implementation &amp; support",
        "scope_title": "What the price covers",
        "scope_licence": "<strong>The module licence only.</strong> Assistance, installation, "
        "configuration, data migration and training are not included and are quoted separately.",
        "scope_used": "<strong>These modules are not shelfware.</strong> We build and maintain them "
        "for our own Odoo implementations &mdash; they run in production at our customers, which is "
        "why they keep up with each Odoo release and with the changes ANAF publishes.",
        "scope_fit": "<strong>Romanian localisation needs fitting to your company.</strong> Chart of "
        "accounts, fiscal positions, journals and reporting practice differ from one company to the "
        "next, so a working setup is a configuration exercise, not just an install.",
        "support_title": "Need help getting started?",
        # ruperile de rând reproduc exact pagina generată înainte de unificare în suitele
        # EN, ca sincronizarea să nu rescrie sute de index.html doar pe spații
        # sub story_body, în același card: invitația la suport, urmată de buton
        "support_body": "Questions about this module, or need it adapted to your processes?\n"
        "     Write to us &mdash; the developers who build it will answer.",
        "support_cta": "Terrabit support &rarr;",
        # ruperile de rând reproduc pagina generată înainte, ca sincronizarea să nu rescrie
        # sute de index.html doar pe spații; titlul cardului e support_title
        "story_body": "Our 350+ apps on the Odoo Apps Store are used in Odoo implementations across Europe,\n"
        "     the Americas, Asia and Africa &mdash; by companies we have never even met. That is the\n"
        "     advantage of building modules that simply work.",
        "cross_title": "More apps by Terrabit",
        "cross_body": "Other modules from the same publisher, built to work together.",
        "cross_all": "All apps &rarr;",
        "badge_hosting": "Odoo.sh &bull; On-premise",
        "rating_free_title": "Did this module help you?",
        "rating_free_body": "It is free, built and maintained by the Terrabit developers. If it saved you time, "
        "a rating on this page is the best way to say thanks &mdash; and it helps other Odoo users find it too. "
        "Thank you for your support!",
        "rating_paid_title": "Happy with this module?",
        "rating_paid_body": "A rating on this page helps other Odoo users find it and tells our developers "
        "what works. Thank you!",
    },
    "ro": {
        "tab_overview": "Prezentare",
        "tab_presentation": "Slide-uri",
        "tab_configure": "Configurare",
        "tab_usage": "Utilizare",
        "tab_versions": "Istoric versiuni",
        "tab_romana": "Română",
        "stat_modules": "Module publicate pe Odoo Apps",
        "stat_partner": "Partener Odoo &mdash; implementare &#537;i suport",
        "scope_title": "Ce acoper&#259; pre&#539;ul",
        "scope_licence": "<strong>Doar licen&#539;a modulului.</strong> Asisten&#539;a, instalarea, "
        "configurarea, migrarea datelor &#537;i instruirea nu sunt incluse &#537;i se "
        "contracteaz&#259; separat.",
        "scope_used": "<strong>Modulele nu stau pe raft.</strong> Le construim &#537;i le "
        "&#238;ntre&#539;inem pentru propriile noastre implement&#259;ri Odoo &mdash; ruleaz&#259; "
        "&#238;n produc&#539;ie la clien&#539;ii no&#537;tri, de aceea &#539;in pasul cu fiecare "
        "serie Odoo &#537;i cu structurile publicate de ANAF.",
        "scope_fit": "<strong>Localizarea rom&#226;neasc&#259; cere potrivire pe firm&#259;.</strong> "
        "Planul de conturi, pozi&#539;iile fiscale, jurnalele &#537;i practica de raportare difer&#259; "
        "de la o firm&#259; la alta, deci o instalare func&#539;ional&#259; e un exerci&#539;iu de "
        "configurare, nu doar o instalare de modul.",
        "support_title": "Ave&#539;i nevoie de ajutor la implementare?",
        "support_body": "Ave&#539;i &#238;ntreb&#259;ri despre modul sau vre&#539;i s&#259; &#238;l adapt&#259;m "
        "proceselor voastre? Scrie&#539;i-ne &mdash; v&#259; r&#259;spund programatorii care &#238;l dezvolt&#259;.",
        "support_cta": "Suport Terrabit &rarr;",
        "story_body": "Cele peste 350 de aplica&#539;ii ale noastre de pe Odoo Apps Store sunt "
        "folosite &#238;n implement&#259;ri Odoo din Europa, America, Asia &#537;i Africa &mdash; de "
        "companii pe care nu le-am cunoscut niciodat&#259;. Acesta e avantajul modulelor care pur &#537;i "
        "simplu func&#539;ioneaz&#259;.",
        "cross_title": "Alte aplica&#539;ii Terrabit",
        "cross_body": "Alte module de la acela&#537;i editor, construite s&#259; lucreze &#238;mpreun&#259;.",
        "cross_all": "Toate aplica&#539;iile &rarr;",
        "badge_hosting": "Odoo.sh &bull; Instalare local&#259; (on-premise)",
        "rating_free_title": "V-a ajutat acest modul?",
        "rating_free_body": "E gratuit, construit &#537;i &#238;ntre&#539;inut de programatorii Terrabit. Dac&#259; v-a economisit timp, "
        "un rating pe aceast&#259; pagin&#259; e cel mai bun mod de a ne mul&#539;umi &mdash; &#537;i &#238;i ajut&#259; pe al&#539;i utilizatori Odoo s&#259; &#238;l g&#259;seasc&#259;. "
        "V&#259; mul&#539;umim pentru sprijin!",
        "rating_paid_title": "Sunte&#539;i mul&#539;umit de acest modul?",
        "rating_paid_body": "Un rating pe aceast&#259; pagin&#259; &#238;i ajut&#259; pe al&#539;i utilizatori Odoo s&#259; &#238;l g&#259;seasc&#259; &#537;i le arat&#259; "
        "programatorilor no&#537;tri ce func&#539;ioneaz&#259; bine. V&#259; mul&#539;umim!",
    },
}

# Fragmentele readme → taburi (ordinea = ordinea taburilor)
TABS = [
    ("overview", ("DESCRIPTION.md", "CONTEXT.md")),
    ("presentation", ("PRESENTATION.md",)),
    ("configure", ("INSTALL.md", "CONFIGURE.md")),
    ("usage", ("USAGE.md",)),
    # Traducerea în română (Cozmin și Dorin, 07.10.2026): doar pentru modulele cu aplicabilitate
    # în România, în fișiere separate *.ro.md, afișate într-un tab propriu. Textul în engleză
    # rămâne curat și primul, cum cere Apps Store.
    ("romana", ("DESCRIPTION.ro.md", "CONFIGURE.ro.md", "USAGE.ro.md")),
    ("versions", ("HISTORY.md",)),
]

# ----------------------------------------------------------------------------- #
# Fragmente HTML — LAYOUT/TEMĂ prin clase Bootstrap; brand-ul verde prin
# `background-color` inline (singurul care supraviețuiește sanitizarea).
# ----------------------------------------------------------------------------- #

# Culoarea de corp: store-ul Odoo Apps randează descrierea pe fundal alb, iar culoarea
# implicită moștenită acolo iese gri-deschis și ilizibilă la font-weight normal.
# Fixăm explicit corpul pe gri-închis (BODY) și textul secundar pe MUTED — ambele
# alese să rămână lizibile pe fundal deschis, nu pe dark (store-ul e doar light).
BODY = TB["body"]
MUTED = TB["muted"]

# `font-weight:400` e obligatoriu: store-ul pune descrierea într-un `.oe_styling_v8`
# care forțează `font-weight:300`. Moștenit, textul mic (cross-sell, stats, note) iese
# subțire și pare gri-decolorat, chiar dacă `color` inline e corect.
# Fundal propriu, explicit alb: în backendul Odoo (Apps > modul) descrierea e randată
# în interiorul temei curente. Pe tema dark, fundalul moștenit e închis, iar culorile
# de text de aici sunt fixate pe închis => text invizibil. Pagina își duce deci propriul
# fundal alb și își resetează variabilele Bootstrap moștenite (body/border/card/nav),
# ca să arate identic pe apps.odoo.com și în backend, light sau dark.
THEME_RESET = (
    "background-color:#ffffff;"
    f"--bs-body-color:{BODY};--bs-body-bg:#ffffff;--bs-emphasis-color:{BODY};"
    "--bs-border-color:#dee2e6;"
    "--bs-card-bg:#ffffff;--bs-card-color:" + BODY + ";--bs-card-border-color:#dee2e6;"
    f"--bs-link-color:{TB['primary']};--bs-link-hover-color:{TB['dark']};"
    f"--bs-nav-link-color:{BODY};--bs-nav-pills-link-active-bg:{TB['primary']};"
    "--bs-nav-pills-link-active-color:#ffffff;"
    "--bs-code-color:#b4266b;--bs-heading-color:" + BODY + ";"
)

WRAP_OPEN = (
    f'<div class="mx-auto px-3 py-3 rounded-4" style="max-width:1100px;font-family:{FONT};'
    f'color:{BODY};font-weight:400;{THEME_RESET}">'
)

HERO = """%(marker)s
<div class="text-center rounded-4 shadow px-4 pt-4 pb-3 mt-2 mb-4" style="background-color:%(primary)s;color:#ffffff;">
  %(icon)s
  <h1 class="fw-bold mb-3" style="color:#ffffff;font-size:42px;line-height:1.08;letter-spacing:-0.5px;border:none;">%(name)s</h1>
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
    '<span class="d-inline-block rounded-pill fw-semibold m-1"'
    ' style="background-color:%(dark)s;color:#ffffff;padding:8px 16px;font-size:12px;">%(t)s</span>'
)
# Versiunea Odoo: aceleași culori ca celelalte insigne (alb pe verde închis, 11.4:1);
# verdele deschis cu text închis nu se distingea pe fundalul verde al cardului.
BADGE_ACCENT = (
    '<span class="d-inline-block rounded-pill fw-bold m-1"'
    ' style="background-color:%(dark)s;color:#ffffff;padding:8px 16px;font-size:12px;">%(t)s</span>'
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

# Panou: NU folosi clasa `text-body` — pe apps.odoo.com ea e definită ca
# `color: rgba(var(--body-color-rgb), 1) !important`, iar `--body-color` al store-ului
# e gri (#374151); fiind `!important`, bate și `color` inline de pe wrapper, deci
# textul iese gri, nu negru. Punem culoarea și greutatea inline pe panou
# (store-ul moștenește `--body-font-weight: 300`, care subțiază textul).
PANEL = """<div class="tab-pane fade%(active)s py-2" id="tb-panel-%(key)s" style="font-size:16px;line-height:1.65;color:%(body_color)s;font-weight:400;">
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
    <div class="border rounded-3 px-4 py-2 h-100">
      <div class="fw-bold" style="font-size:2.2rem;color:%(primary)s;line-height:1;">%(big)s</div>
      <div class="mt-2" style="font-size:0.9rem;color:%(muted)s;">%(small)s</div>
    </div>
  </div>"""
# Date factuale despre autor (numărul de module publicate și întreținute pe Apps, nivelul
# de parteneriat), nu promoții sau reclame în sensul vendor guidelines.
STAT_ITEMS = [
    ("350+", "stat_modules"),
    ("Silver", "stat_partner"),
]

# Delimitarea comercială: ce acoperă prețul de pe Apps Store și ce nu. Blocul stă
# ÎNAINTE de CTA-ul de suport, ca cititorul să afle limita înainte de invitație.
# Ton informativ, nu defensiv — nu e disclaimer legal, licența OPL-1 rămâne sursa.
# Textul vorbește despre localizarea RO și ANAF, deci apare doar cu --scope-note
# (l10n_ro_ent); celelalte suite nu îl primesc.
SCOPE_NOTE = """
<section class="rounded-4 p-4 mt-4 mb-3 border">
  <h2 class="fw-bold mb-3" style="font-size:20px;border:none;color:%(body)s;">%(scope_title)s</h2>
  <ul class="mb-0 ps-4" style="color:%(body)s;line-height:1.7;font-size:15px;">
    <li>%(scope_licence)s</li>
    <li>%(scope_used)s</li>
    <li>%(scope_fit)s</li>
  </ul>
</section>
"""

# Butonul: verde pal #DEF1DD (ca la caseta de rating) cu text verde închis, 9.7:1 pe cardul
# închis; verdele accent cu text închis se pierdea vizual.
SUPPORT = """
<div class="text-center rounded-4 px-4 pt-3 pb-4 mt-4 mb-3" style="background-color:%(dark)s;color:#ffffff;">
  <h2 class="fw-bold mb-2" style="color:#ffffff;font-size:26px;letter-spacing:-0.3px;border:none;">%(support_title)s</h2>
  <p class="mx-auto mb-2" style="color:#bfe3cc;max-width:660px;line-height:1.6;font-size:16px;">
     %(story_body)s</p>
  <p class="mx-auto mb-4" style="color:#bfe3cc;max-width:660px;line-height:1.6;font-size:16px;">
     %(support_body)s</p>
  <a href="%(contact_url)s" target="_blank" rel="noopener"
     class="d-inline-block fw-bold text-decoration-none rounded-3"
     style="background-color:#DEF1DD;color:%(dark)s;padding:14px 32px;font-size:15px;">%(support_cta)s</a>
</div>
"""

# Cerere de rating, imediat sub hero. Vendor guidelines interzic doar alterarea
# artificială a clasamentului (stimulente, cumpărări proprii) — o rugăminte simplă, fără
# nimic la schimb, e în regulă. Textul diferă după cum modulul e gratuit sau plătit.
RATING = """
<div class="d-flex align-items-start rounded-4 px-4 py-3 mb-4" style="background-color:#DEF1DD;color:%(body)s;">
  <span class="flex-shrink-0 me-3" style="font-size:26px;line-height:1.2;color:%(primary)s;">&#9733;</span>
  <div style="font-size:16px;line-height:1.55;">
    <span class="fw-bold" style="color:%(primary)s;">%(title)s</span> %(text)s
  </div>
</div>
"""

CROSS_SELL_OPEN = """
<section class="rounded-4 p-4 mb-3 border">
  <h2 class="text-center fw-bold mb-1" style="color:%(body)s;font-size:24px;border:none;">%(cross_title)s</h2>
  <p class="text-center mb-4" style="color:%(muted)s;">%(cross_body)s
    <a href="https://apps.odoo.com/apps/browse?author=%(apps_author)s" target="_blank" rel="noopener"
       class="fw-semibold" style="color:%(primary)s;">%(cross_all)s</a></p>
  <div class="row g-3">
"""
CROSS_SELL_CARD = """    <div class="col-md-3 col-sm-6">
      <a href="https://apps.odoo.com/apps/modules/%(series)s/%(tech)s" target="_blank" rel="noopener"
         class="card h-100 text-decoration-none border" style="color:%(body)s;">
        <div class="card-body p-3">
          <div class="d-flex align-items-center mb-2">
            <span class="d-inline-block position-relative me-2 flex-shrink-0" style="width:40px;height:40px;">
              <span class="d-inline-block text-center fw-bold rounded"
                    style="width:40px;height:40px;line-height:40px;font-size:14px;color:#ffffff;background-color:%(primary)s;">%(initials)s</span>
              <img src="https://apps.odoocdn.com/apps/assets/%(series)s/%(tech)s/icon.png" alt="" loading="lazy"
                   class="position-absolute top-0 start-0 rounded" style="width:40px;height:40px;border:none;background-color:#ffffff;"/>
            </span>
            <span>
              <span class="d-block fw-semibold" style="font-size:16px;line-height:1.25;">%(name)s</span>
              <span class="d-block" style="font-size:13px;color:%(muted)s;">%(category)s</span>
            </span>
          </div>
          <p class="mb-0" style="font-size:15px;line-height:1.45;color:%(muted)s;">%(summary)s</p>
        </div>
      </a>
    </div>
"""
CROSS_SELL_CLOSE = "  </div>\n</section>\n"

# --- carduri de funcții (grilă Bootstrap responsivă), moștenite din tb_skin_index v5 --- #
# Casete compacte (Cozmin, 06.10.2026): 8px sus/jos și 16px lateral în casetă, 8px între casete,
# lista imbricată lipită de titlu; aceleași setări pentru toate grilele (Key Features, Benefits...).
UL_GRID = "list-unstyled row row-cols-1 row-cols-md-2 g-2 mt-1 mb-4"
CARD = "border rounded-3 px-3 py-2 h-100"
BADGE_TICK = "flex-shrink-0 text-center fw-bold rounded d-inline-block"
BADGE_TICK_STYLE = (
    f"background-color:{TB['accent']};color:#04331f;width:22px;height:22px;line-height:22px;font-size:13px;"
)
SUB_UL = "ps-3 mt-1 mb-0"
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


def _dependency_closure(name, addons_root, seen=None):
    """Modulul și dependențele lui din aceeași suită (tranzitiv, în ordine DFS)."""
    seen = seen if seen is not None else []
    if name in seen or not read_manifest(os.path.join(addons_root, name)):
        return seen
    seen.append(name)
    for dep in read_manifest(os.path.join(addons_root, name)).get("depends") or []:
        _dependency_closure(dep, addons_root, seen)
    return seen


def read_framework_features(addon_dir):
    """Fragmentele FRAMEWORK_FEATURES.md ale modulelor de care depinde acest modul
    (direct sau tranzitiv, ex. deltatech_marketplace_sale_stage -> ...sale ->
    ...marketplace), sau ale lui însuși."""
    addon_dir = os.path.normpath(addon_dir)
    addons_root = os.path.dirname(addon_dir) or "."
    chunks = []
    for name in _dependency_closure(os.path.basename(addon_dir), addons_root):
        chunk = read_fragment(os.path.join(addons_root, name), FRAMEWORK_FRAGMENT)
        if chunk:
            chunks.append(chunk)
    return "\n\n".join(chunks)


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
        '<p class="mb-4" style="font-size:16px;line-height:1.65;max-width:780px;">',
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
                f'<li class="col"><div class="{CARD}"><span class="fw-bold">{lead}</span><div>{rest}</div></div></li>'
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


def build_badges(manifest, lang="en"):
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
    # modulele terțe cu cod Python nu rulează pe Odoo Online (Apps FAQ)
    items.append((BADGE, I18N[lang]["badge_hosting"]))
    return "\n    ".join(tmpl % dict(TB, t=t) for tmpl, t in items)


def build_hero(addon_dir, manifest, lang="en"):
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
        badges=build_badges(manifest, lang),
    )


def build_tab_sources(addon_dir, manifest, allow_ro=False, lang="en"):
    """Întoarce [(key, title, markdown)] doar pentru taburile cu fragment existent."""
    name = manifest.get("name") or ""
    tabs = []
    strings = I18N[lang]
    for key, files in TABS:
        title = strings[f"tab_{key}"]
        chunks = [read_fragment(addon_dir, fn) for fn in files]
        if key == "romana":
            # un singur tab în română, cu câte un subtitlu pentru fiecare fișier existent
            heads = ("Prezentare", "Configurare", "Utilizare")
            chunks = [f"### {h}\n\n{c}" if c else c for h, c in zip(heads, chunks, strict=False)]
        if key == "overview":
            chunks.append(read_framework_features(addon_dir))
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


def style_images(rendered):
    """Imaginile (slide-urile din tabul Presentation) pe toată lățimea, cu ramă."""
    return re.sub(
        r"<img ",
        '<img class="img-fluid rounded-3 border shadow-sm d-block mx-auto" style="width:100%;height:auto;" ',
        rendered,
    )


def fix_image_paths(rendered):
    """Căile imaginilor relative la index.html, nu la rădăcina modulului.

    readme/*.md scrie `static/description/x.png`, corect pentru README.rst de pe GitHub.
    index.html stă chiar în static/description/, iar Apps Store rescrie spre CDN doar
    numele simple de fișier — cu prefixul, imaginea dă 404 pe pagina publicată.
    """
    return re.sub(r'(<img\b[^>]*?\bsrc=")(?:\.\./|\./)?static/description/', r"\1", rendered)


def build_panel_body(key, md_text):
    rendered = render_markdown(md_text)
    rendered = fix_image_paths(rendered)
    rendered = style_tables(rendered)
    rendered = style_code(rendered)
    if key == "presentation":
        rendered = style_images(rendered)
    if key in ("overview", "romana"):
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
        if key == "romana":
            # tabul se numește deja „Română”: titlul ar repeta numele tabului, iar
            # subtitlurile Prezentare / Configurare / Utilizare țin loc de titlu
            heading = ""
        panes.append(
            PANEL
            % {
                "active": " show active" if i == 0 else "",
                "key": key,
                "heading": heading,
                "body_color": BODY,
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


def build_cross_sell(addon_dir, manifest, count=CROSS_SELL_COUNT, lang="en"):
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
    return (CROSS_SELL_OPEN % dict(TB, **I18N[lang])) + "".join(cards) + CROSS_SELL_CLOSE


def build_rating(manifest, lang="en"):
    strings = I18N[lang]
    kind = "paid" if manifest.get("price") else "free"
    return RATING % dict(TB, title=strings[f"rating_{kind}_title"], text=strings[f"rating_{kind}_body"])


def build_stats(lang="en"):
    if not STAT_ITEMS:
        return ""
    strings = I18N[lang]
    col = max(3, 12 // max(1, len(STAT_ITEMS)))
    cards = "\n  ".join(STAT_CARD % dict(TB, big=big, small=strings[key], col=col) for big, key in STAT_ITEMS)
    return STATS % {"cards": cards}


def gen_index(addon_dir, cross_sell=True, allow_ro=False, lang="en", scope_note=False):
    manifest = read_manifest(addon_dir)
    tabs = build_tab_sources(addon_dir, manifest, allow_ro=allow_ro, lang=lang)
    strings = dict(TB, **I18N[lang])
    parts = [
        WRAP_OPEN,
        build_hero(addon_dir, manifest, lang),
        build_rating(manifest, lang),
        build_tabs(tabs),
        build_stats(lang),
        (SCOPE_NOTE % strings) if scope_note else "",
        SUPPORT % strings,
        build_cross_sell(addon_dir, manifest, lang=lang) if cross_sell else "",
        "</div>\n",
    ]
    return "\n".join(p for p in parts if p)


# ----------------------------------------------------------------------------- #
# CLI
# ----------------------------------------------------------------------------- #


def ascii_safe(text):
    """Transformă orice caracter non-ASCII în entitate HTML numerică.

    Store-ul Odoo Apps despachetează fragmentul și îl re-servește fără să respecte
    charset-ul nostru, așa că un em-dash sau o diacritică scrise ca UTF-8 brut ajung
    citite ca latin-1 și afișate mojibake (â€"). Entitățile numerice sunt imune.
    """
    return "".join(c if ord(c) < 128 else f"&#{ord(c)};" for c in text)


def may_overwrite(index_path):
    if not os.path.exists(index_path):
        return True
    with open(index_path, encoding="utf8") as f:
        existing = f.read()
    return any(marker in existing for marker in KNOWN_MARKERS)


def process(addon_dir, cross_sell=True, force=False, allow_ro=False, lang="en", scope_note=False):
    if not read_manifest(addon_dir):
        return False
    if not read_fragment(addon_dir, "DESCRIPTION.md"):
        _logger.info("[tb-gen] SKIP %s: fără readme/DESCRIPTION.md", addon_dir)
        return False
    desc_dir = os.path.join(addon_dir, "static", "description")
    index_path = os.path.join(desc_dir, "index.html")
    if not force and not may_overwrite(index_path):
        _logger.info("[tb-gen] SKIP %s: index.html manual (folosește --force)", index_path)
        return False
    # generează ÎNAINTE de a deschide fișierul — o eroare la generare nu trebuie
    # să lase un index.html trunchiat
    content = ascii_safe(
        gen_index(addon_dir, cross_sell=cross_sell, allow_ro=allow_ro, lang=lang, scope_note=scope_note)
    )
    os.makedirs(desc_dir, exist_ok=True)
    with open(index_path, "w", encoding="utf8") as f:
        f.write(content)
    _logger.info("[tb-gen] %s", index_path)
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
    ap.add_argument(
        "--lang",
        choices=sorted(I18N),
        default="en",
        help="limba textelor generate (taburi, stats, note, CTA); `ro` implică --allow-ro",
    )
    ap.add_argument(
        "--scope-note",
        action="store_true",
        help="adaugă nota „ce acoperă prețul” (text scris pentru localizarea RO, l10n_ro_ent)",
    )
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

    targets = list(args.addon_dir)
    if args.addons_dir:
        targets += list(find_addons(args.addons_dir))
    if not targets:
        targets = list(find_addons("."))

    count = sum(
        1
        for d in targets
        if process(
            d,
            cross_sell=not args.no_cross_sell,
            force=args.force,
            # o pagină în RO include implicit HISTORY-ul scris în română: filtrul de
            # diacritice există ca să nu urce text RO pe o pagină EN, nu invers.
            allow_ro=args.allow_ro or args.lang == "ro",
            lang=args.lang,
            scope_note=args.scope_note,
        )
    )
    _logger.info("[tb-gen] gata: %s module generate.", count)


if __name__ == "__main__":
    main()
