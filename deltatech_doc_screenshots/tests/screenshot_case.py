# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""Mixin reutilizabil pentru generarea capturilor de ecran din fișele consultant.

Folosește infrastructura `HttpCase` a Odoo (server + browser pe tranzacția testului) și
**Playwright** (Chrome de sistem, `channel="chrome"`) pentru navigare și capturi cu nume
curate, scrise direct în `<modul>/static/description/` (sau în `readme/screenshots/`, cât timp
modulul îl mai are).

Utilizare într-un modul (import defensiv: dacă acest modul de tooling lipsește de pe disc,
testul de capturi nu se definește, fără să strice încărcarea suitei modulului consumator):

    from odoo.tests import tagged

    try:
        from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
    except ImportError:
        ScreenshotCase = None

    @tagged("-at_install", "post_install", "fise_screenshots")
    class TestXScreenshots(ScreenshotCase or object):
        screenshots_module = "l10n_ro_x"

        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            ...  # seedează date determinist

        def test_capture_fise(self):
            self.capture_screenshots([
                {"url": f"action={self.act}&view_type=list", "name": "01_lista.png", "wait": ".o_list_view"},
                {"url": f"action={self.act}&id={rec}&model=x&view_type=form", "name": "02_form.png", "full": True},
            ])

Capturi în două limbi (fișa consultant în RO, ``readme/USAGE.md`` pentru Apps Store în EN):
aceeași listă de shot-uri, câte o metodă per limbă. Capturile RO rămân în folderul obișnuit,
cele EN ajung în ``static/description/en/`` (vezi ``screenshots_dir``):

        def _shots(self):
            return [...]

        def test_capture_fise(self):
            self.capture_screenshots(self._shots())  # ro_RO

        def test_capture_usage(self):
            self.capture_screenshots(self._shots(), lang="en_US")

Rulare:

    ./odoo/odoo-bin -c odoo.conf -d <db> -i l10n_ro_x --test-tags=fise_screenshots --stop-after-init

Dependențe de tooling (nu module Odoo): `playwright` și `websocket-client` în mediul Odoo
(`uv pip install --python .venv/bin/python playwright websocket-client`) + Chrome de sistem.
Dacă `playwright` lipsește, testul se sare (nu eșuează).

Reguli de conținut pentru fișe:
  - câte o captură pentru fiecare pas din secțiunea „Flux de utilizare" (de încercat; dacă un
    pas nu are un ecran propriu relevant, reutilizează cel mai apropiat sau notează lipsa);
  - notele contabile se afișează mereu în detaliu, cu liniile Dr/Cr (``account_move_shot``);
  - capturile se fac pe compania „RO Company" în RON (``prepare_ro_company``).
"""

import contextlib
import json
import logging
import os
import unittest
from urllib.parse import quote

from odoo.modules.module import get_module_path
from odoo.tests.common import HttpCase
from odoo.tests.tag_selector import TagsSelector
from odoo.tools import config

_logger = logging.getLogger(__name__)

DEFAULT_READY = ".o_form_view, .o_list_view"

#: etichetele RO ale tab-urilor cerute prin ``click_tab`` cu numele lor englezesc
TAB_LABELS_RO = {
    "Journal Items": "Elemente jurnal",
    "Invoice Lines": "Linii factură",
    "Other Info": "Alte informații",
}

#: limba capturilor fișei consultant; celelalte limbi au subfolderul lor (``en/``)
DEFAULT_LANG = "ro_RO"

#: ``report_shot`` fără limbă explicită: raportul se randează în limba capturii curente
AUTO_LANG = "auto"


def _is_lang_map(value):
    """Spune dacă ``value`` e o valoare dependentă de limbă: ``{"ro_RO": ..., "en_US": ...}``."""
    return (
        isinstance(value, dict)
        and bool(value)
        and all(isinstance(k, str) and len(k) == 5 and k[2] == "_" for k in value)
    )


def _for_lang(value, lang):
    """Alege varianta pentru ``lang`` dintr-o valoare dependentă de limbă; altfel o lasă neatinsă.

    Folosit pe selectoarele care conțin text din interfață (``button:has-text('Confirmă')``),
    care nu se mai potrivesc când capturile se fac în altă limbă. Dacă limba lipsește din
    dicționar se ia varianta ``en_US``, apoi prima.
    """
    if _is_lang_map(value):
        return value.get(lang) or value.get("en_US") or next(iter(value.values()))
    if isinstance(value, list):
        return [_for_lang(v, lang) for v in value]
    return value


@contextlib.contextmanager
def _unlimited_address_space():
    """Ridică temporar limita de memorie virtuală (RLIMIT_AS) pusă de Odoo (`limit_memory_hard`).

    Chrome rezervă mult spațiu virtual la pornire; cu limita lui Odoo moștenită, cel pornit de
    Playwright moare imediat (SIGTRAP, „Target page, context or browser has been closed").
    Browserul de teste al lui Odoo ridică limita singur (`_preexec` din odoo.tests.common),
    Playwright nu: o ridicăm noi cât timp rulează driverul, care pornește Chrome. Doar
    limita soft, până la cea hard, fără drepturi speciale; pe macOS nu se aplică.
    """
    try:
        import resource  # noqa: PLC0415
    except ImportError:  # Windows
        yield
        return
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    if soft == hard:
        yield
        return
    resource.setrlimit(resource.RLIMIT_AS, (hard, hard))
    try:
        yield
    finally:
        resource.setrlimit(resource.RLIMIT_AS, (soft, hard))


class ScreenshotCase(HttpCase):
    """Bază pentru testele de capturi. Subclasele setează ``screenshots_module``."""

    #: numele tehnic al modulului în care se scriu pozele (readme/screenshots)
    screenshots_module = None

    @classmethod
    def setUpClass(cls):
        # Capturile sunt artefacte de documentație (HttpCase + Playwright, lente), nu teste
        # de corectitudine -- și, spre deosebire de un test, ele SCRIU în arborele de lucru:
        # rescriu .png-urile din ``<modul>/static/description`` ale fiecărui modul atins.
        # De aceea se generează doar când rularea le cere explicit (vezi
        # ``_screenshots_requested``); orice altă rulare de teste le sare, ca să nu producă
        # diff-uri binare nedorite în mijlocul altei modificări. Sărim înainte de
        # ``super()`` ca să evităm și seeding-ul greoi din ``setUpClass`` al subclaselor.
        if os.environ.get("SKIP_FISE_SCREENSHOTS"):
            raise unittest.SkipTest("Capturi fișe sărite (SKIP_FISE_SCREENSHOTS).")
        if not cls._screenshots_requested():
            raise unittest.SkipTest(
                "Capturile se generează doar la cerere: rulează cu "
                "--test-tags=fise_screenshots (sau numind clasa, ori cu FISE_SCREENSHOTS=1)."
            )
        super().setUpClass()

    @classmethod
    def _screenshots_requested(cls):
        """Spune dacă rularea curentă a cerut *explicit* generarea capturilor.

        „Explicit" înseamnă una dintre:

        * un tag propriu al clasei care se termină în ``_screenshots`` apare în
          ``--test-tags`` (``fise_screenshots``, ``shopify_screenshots``, ...);
        * ``--test-tags`` numește clasa (``/modul:TestXScreenshots``);
        * ``FISE_SCREENSHOTS`` e setat în mediu, pentru scripturile care rulează
          generarea altfel decât prin taguri.

        O rulare obișnuită -- ``-u modul --test-tags=/modul``, sau rularea completă a
        suitei -- NU cere capturi, deci acestea se sar. Spec-ul e citit cu parserul
        Odoo (``TagsSelector``), ca să nu ne diverge propria interpretare de a lui.
        """
        if os.environ.get("FISE_SCREENSHOTS"):
            return True
        spec = config["test_tags"]
        if not spec:
            return False
        own_tags = {tag for tag in getattr(cls, "test_tags", ()) or () if tag.endswith("_screenshots")}
        for tag, _module, klass, _method, _file_path in TagsSelector(spec).include:
            if (tag and tag in own_tags) or klass == cls.__name__:
                return True
        return False

    @classmethod
    def activate_ro_lang(cls):
        """Activează limba **română** și o setează pe admin, astfel încât capturile să
        prezinte interfața în RO (cerință pentru fișele consultant).

        Rulează **întotdeauna** ``base.language.install`` (cu ``overwrite=False``), nu doar
        când ``ro_RO`` e inactivă. Motivul: activarea limbii (``active = True``) și
        **încărcarea termenilor** sunt două lucruri diferite. Termenii de cod (Python/JS) se
        citesc direct din ``.po`` de pe disc, deci ies în RO oricum; termenii de
        view/câmp/date stau în coloane ``jsonb`` în bază și există doar dacă
        ``ir.module.module._update_translations`` a rulat pentru modulul respectiv. Cum
        ``setup_country("ro")`` / ``l10n_ro`` activează singure ``ro_RO``, garda anterioară
        ``if not lang.active`` sărea încărcarea și capturile ieșeau **mixte** (butoane și
        etichete de câmp în engleză peste un chrome RO).

        ``overwrite=False`` păstrează traducerile deja prezente și completează doar ce
        lipsește, deci reapelarea e idempotentă. Apelat automat din ``prepare_ro_company`` /
        ``prepare_demo_company``. No-op dacă limba nu poate fi activată.
        """
        cls.activate_lang(DEFAULT_LANG)

    @classmethod
    def activate_lang(cls, code, user=None):
        """Activează limba ``code``, îi încarcă termenii și o setează pe ``user`` (implicit admin).

        Vezi ``activate_ro_lang`` pentru de ce instalarea termenilor rulează mereu. ``en_US``
        e limba sursă a termenilor, deci nu are ce instala: doar se setează pe utilizator.
        No-op dacă limba nu poate fi activată.
        """
        env = cls.env
        try:
            if code != "en_US":
                lang = env["res.lang"].with_context(active_test=False).search([("code", "=", code)], limit=1)
                if lang:
                    # activează limba (dacă nu e) + încarcă termenii tuturor modulelor instalate
                    env["base.language.install"].create(
                        {"lang_ids": [(6, 0, lang.ids)], "overwrite": False}
                    ).lang_install()
            (user or env.ref("base.user_admin")).lang = code
            env.flush_all()
        except Exception:  # noqa: BLE001 - dacă limba nu e disponibilă, rămânem pe EN
            _logger.debug("Screenshots: limba %s nu e disponibilă, rămânem pe EN", code, exc_info=True)

    @classmethod
    def force_light_theme(cls):
        """Forțează tema **luminoasă** pentru admin, ca tabelele rapoartelor (account.report)
        și formularele să iasă pe fundal alb în capturi — lizibil într-o fișă consultant —
        indiferent de preferința stocată în baza de date (Enterprise: tema din
        ``res_users_settings_id.color_scheme`` învinge cookie-ul). Apelat automat din
        ``prepare_ro_company`` / ``prepare_demo_company``. No-op dacă modelul lipsește.
        """
        env = cls.env
        try:
            admin = env.ref("base.user_admin")
            settings = env["res.users.settings"]._find_or_create_for_user(admin)
            if "color_scheme" in settings._fields:
                settings.color_scheme = "light"
                env.flush_all()
        except Exception:  # noqa: BLE001 - fără modelul de settings (Community) rămânem pe default
            _logger.debug("Screenshots: fără modelul de settings (Community) rămânem pe default", exc_info=True)

    @classmethod
    def prepare_ro_company(cls, name="RO Company"):
        """Pregătește compania pentru capturi: nume RO, țară RO, monedă RON și drepturi
        contabile pentru admin (ca tab-ul „Journal Items" să fie vizibil în capturi).

        Identitatea companiei se maschează **complet** — nu doar numele de pe
        ``res.company``. Capturile se generează uneori pe o copie a bazei unui client,
        pentru că doar acolo există un plan de conturi RO real, iar imaginile ajung în
        `static/description` din repo. Fără mascarea completă rămâneau la vedere NRC-ul,
        IBAN-ul, telefonul și județul reale, iar pe același document apăreau **două
        identități**: antetul layoutului citește partenerul companiei, corpul citește
        compania — deci antetul păstra numele real, iar corpul îl arăta pe cel mascat.

        Returnează compania. De apelat la începutul lui ``setUpClass`` (după ``super()``).
        """
        env = cls.env
        company = env.company
        state_ro_b = env["res.country.state"].search(
            [("country_id", "=", env.ref("base.ro").id), ("code", "=", "B")], limit=1
        )
        company.write(
            {
                "name": name,
                "country_id": env.ref("base.ro").id,
                # Date complete ca să nu apară bannerul galben „definiți ID-ul companiei,
                # telefon, oraș/cod poștal" în capturi (date RO plauzibile pentru manual).
                "vat": "RO14388698",
                "company_registry": "J40/1234/2020",
                "street": "Str. Exemplu nr. 10",
                "street2": False,  # pe bazele reale conținea etajul/biroul clientului
                "city": "București",
                "zip": "010101",
                "phone": "+40 21 123 4567",
                "email": "office@example.ro",
                # județul rămânea cel real (ex. „București IS" pe o bază copiată din Iași)
                **({"state_id": state_ro_b.id} if state_ro_b else {}),
                # footerul e text liber pe companie: pe bazele reale conținea alt telefon
                # și alt CUI decât cele mascate mai sus
                "report_footer": "Document generat pentru documentație — date de exemplu.",
                # `company_details` e instantaneul HTML al identității companiei, salvat de
                # wizardul de layout și tipărit în antetul rapoartelor. NU se recalculează
                # din câmpurile de adresă, deci pe o bază reală antetul păstra numele și
                # adresa clientului chiar cu tot restul documentului mascat.
                # fără CUI aici: layoutul îl tipărește deja separat, altfel apare de două ori
                "company_details": (f"<p>{name}<br/>Str. Exemplu nr. 10<br/>București 010101<br/>România</p>"),
            }
        )
        # Antetul layoutului (ex. `external_layout_boxed`) citește PARTENERUL companiei,
        # iar numele și adresa nu se sincronizează integral din `res.company`: le scriem
        # explicit, altfel antetul păstrează identitatea reală a clientului chiar dacă
        # restul documentului e mascat.
        partner_vals = {
            "name": name,
            # CIF-ul se scrie ȘI pe partener, pentru că rapoartele RO îl tipăresc de acolo, nu
            # de pe companie. Atenție: `base_vat` normalizează valoarea și taie prefixul de
            # țară când coincide cu țara partenerului, deci pe documente CIF-ul apare
            # „14388698", nu „RO14388698" — prefixul nu se poate impune de aici.
            "vat": "RO14388698",
            "street": "Str. Exemplu nr. 10",
            "street2": False,
            "city": "București",
            "zip": "010101",
            "country_id": env.ref("base.ro").id,
            "phone": "+40 21 123 4567",
            "email": "office@example.ro",
        }
        if state_ro_b:
            partner_vals["state_id"] = state_ro_b.id
        if "nrc" in company.partner_id._fields:  # NRC (l10n_ro) — tipărit de rapoartele RO
            partner_vals["nrc"] = "J40/1234/2020"
        company.partner_id.write(partner_vals)
        # IBAN-ul apare pe factură („pe acest cont: …"). Mascăm primul cont cu IBAN-ul
        # de test RO și arhivăm restul: pe un singur cont nu se încalcă unicitatea
        # numărului, iar factura tot are ce tipări.
        banks = env["res.partner.bank"].search([("partner_id", "=", company.partner_id.id)])
        if banks:
            try:
                banks[0].acc_number = "RO49AAAA1B31007593840000"
                banks[1:].active = False
            except Exception:  # noqa: BLE001 - IBAN validat/constrâns: capturile merg și fără
                _logger.debug("Screenshots: IBAN validat/constrâns: capturile merg și fără", exc_info=True)
        ron = env["res.currency"].with_context(active_test=False).search([("name", "=", "RON")], limit=1)
        if ron:
            ron.active = True
            try:
                company.currency_id = ron.id
            except Exception:  # noqa: BLE001 - dacă există deja note contabile
                _logger.debug("Screenshots: dacă există deja note contabile", exc_info=True)
        admin = env.ref("base.user_admin")
        for xmlid in ("account.group_account_readonly", "account.group_account_user", "account.group_account_manager"):
            grp = env.ref(xmlid, raise_if_not_found=False)
            if grp:
                admin.group_ids = [(4, grp.id)]
        env.flush_all()
        cls.activate_ro_lang()
        cls.force_light_theme()
        cls.align_website_company(company)
        return company

    @classmethod
    def align_website_company(cls, company=None):
        """Aliniază compania site-ului la compania capturilor. No-op fără modulul ``website``.

        ``/report/html/...`` (ruta folosită de ``report_shot``) e o rută de **website**, iar
        acolo ``self.env.company`` din randarea raportului vine de la **compania site-ului**,
        nu din ``allowed_company_ids``. Pe o companie creată de test, raportul citește deci
        identitatea altei companii. De aici două simptome văzute în practică, ambele **fără
        ca testul să pice** — captura salvată era pur și simplu greșită:

        - **403 Interzis** pe documentele companiei de test (regulile multi-companie);
        - documentul randat în **engleză**, când șablonul alege limba din
          ``res_company.partner_id.lang`` (cazul facturii „în limba companiei").
        """
        env = cls.env
        if "website" not in env:
            return
        websites = env["website"].sudo().search([])
        if websites:
            websites.company_id = (company or env.company).id
            env.flush_all()

    def account_move_shot(self, move, name, click_tab="Journal Items", full=True):
        """Construiește un element de captură pentru formularul unei note contabile.

        Deschide ``account.move`` în formular și dă click pe tab-ul „Journal Items" ca să
        se vadă liniile Dr/Cr. Necesită ca utilizatorul să aibă drepturi contabile — folosiți
        ``prepare_ro_company()`` (care le acordă) în ``setUpClass``.

        Documentul se deschide prin acțiunea de jurnal, nu prin ``id=…&model=…``: fără
        acțiune, breadcrumb-ul afișează chip-ul „Nou(ă)" chiar și pe o notă postată, ceea
        ce derutează într-un manual.

        Utilizare:
            shots.append(self.account_move_shot(self.move, "05_nota.png"))
        """
        move_id = getattr(move, "id", move)
        action = self.env.ref("account.action_move_journal_line", raise_if_not_found=False)
        url = (
            f"action={action.id}&id={move_id}&model=account.move&view_type=form"
            if action
            else f"id={move_id}&model=account.move&view_type=form"
        )
        return {
            "url": url,
            "name": name,
            "full": full,
            "click_tab": click_tab,
            "wait": ".o_form_view",
        }

    @classmethod
    def report_shot(
        cls, report_ref, res_id, name, wait="body", full=True, settle=2000, lang=AUTO_LANG, companies=None, **extra
    ):
        """Construiește un element de captură pentru un **raport tipăribil (PDF)**, randându-l HTML.

        Folosește ruta ``/report/html/<report_ref>/<res_id>``, care produce **exact layout-ul
        PDF-ului tipărit** dar randat în browser — captura arată documentul generat (factură, NIR,
        aviz, declarație) așa cum iese la print, fără a depinde de wkhtmltopdf în mediul de test.

        ``report_ref`` e referința raportului (``action_report``), ex. ``"account.report_invoice"``
        sau ``"modul.report_xxx"``. ``res_id`` poate fi un id sau un recordset (se ia ``.id``).

        ``companies`` (implicit compania testului) forțează ``allowed_company_ids`` pe randare.
        Necesar de când capturile se fac pe o companie creată de test (``setup_country`` +
        ``prepare_ro_company``): ``/report/html`` e o rută de website, iar regulile de acces
        multi-companie evaluează ``allowed_company_ids`` din contextul cererii, nu compania
        implicită a utilizatorului — fără forțare raportul iese **403 Interzis**, iar captura
        salvată e pagina de eroare, fără ca testul să pice. Treci ``companies=False`` ca să
        lași rezoluția implicită, sau un recordset ``res.company`` pentru alt set.

        ``lang`` forțează limba de randare a raportului. Necesar pentru fișe: ``/report/html`` este
        o rută ``website=True``, iar cu modulul ``website`` instalat middleware-ul de website impune
        limba IMPLICITĂ a site-ului (de regulă ``en_US``) pe rutele frontend, ignorând limba
        utilizatorului — așa că, fără forțare, raportul ar ieși în engleză chiar dacă admin-ul e pe
        ``ro_RO``. Transmitem limba prin ``?context={"lang": ...}``, pe care controllerul raportului
        îl aplică (``report_routes`` face ``context.update``). Implicit (``"auto"``) se folosește
        limba capturii (``capture_screenshots(lang=...)``), ca același shot să iasă în RO pentru
        fișă și în EN pentru USAGE.md. Un cod de limbă o fixează; ``lang=None`` lasă rezoluția
        implicită (limba site-ului).

        Utilizare:
            shots.append(self.report_shot("l10n_ro_x.report_xxx", self.doc, "06_raport_pdf.png"))
        """
        rid = getattr(res_id, "id", res_id)
        path = f"/report/html/{report_ref}/{rid}"
        context = {}
        if lang and lang != AUTO_LANG:
            context["lang"] = lang
        if companies is not False:
            records = companies if companies is not None else cls.env.company
            context["allowed_company_ids"] = [getattr(c, "id", c) for c in records]
        shot = {"name": name, "wait": wait, "full": full, "settle": settle}
        if lang == AUTO_LANG:
            # calea finală (cu limba capturii) o construiește ``capture_screenshots``
            shot.update({"report_path": path, "report_context": context})
        else:
            shot["path"] = path + ("?context=" + quote(json.dumps(context)) if context else "")
        shot.update(extra)
        return shot

    @staticmethod
    def xlsx_to_html(source, sheet=0, max_rows=60, max_cols=20, title=None):
        """Randează prima foaie a unui **XLSX generat** ca tabel HTML stilizat (pentru ``xlsx_shot``).

        ``source`` poate fi: o cale pe disc, un ``bytes`` cu conținutul XLSX, sau un ``str`` base64
        (ex. ``report_action`` care întoarce ``file_content``). Citește cu ``openpyxl`` (deja în
        Odoo). Prima linie e tratată ca antet (bold, fundal gri). Truncază la ``max_rows``/``max_cols``
        cu o notă vizibilă, ca să nu producă imagini uriașe. Întoarce un string HTML complet.
        """
        import base64
        import io

        from openpyxl import load_workbook

        if isinstance(source, str) and not os.path.exists(source):
            source = base64.b64decode(source)
        data = source if isinstance(source, (bytes, bytearray)) else open(source, "rb").read()
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.worksheets[sheet] if isinstance(sheet, int) else wb[sheet]

        def esc(v):
            if v is None:
                return ""
            return str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        rows = list(ws.iter_rows(values_only=True))
        truncated_rows = len(rows) > max_rows
        rows = rows[:max_rows]
        ncols = min(max(((len(r) for r in rows)), default=0), max_cols)
        cap = esc(title or ws.title)

        cells = []
        for i, row in enumerate(rows):
            tag = "th" if i == 0 else "td"
            tds = "".join(f"<{tag}>{esc(c)}</{tag}>" for c in list(row)[:ncols])
            cells.append(f"<tr>{tds}</tr>")
        body = "\n".join(cells)
        note = (
            f"<div class='note'>… tabel truncat la {max_rows} rânduri × {max_cols} coloane</div>"
            if truncated_rows
            else ""
        )
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'><style>
            body{{margin:0;padding:16px;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:#fff;}}
            h3{{margin:0 0 10px;font-size:15px;color:#374151;}}
            table{{border-collapse:collapse;font-size:12px;}}
            th,td{{border:1px solid #d1d5db;padding:4px 8px;text-align:left;white-space:nowrap;}}
            th{{background:#f3f4f6;font-weight:700;}}
            tr:nth-child(even) td{{background:#fafafa;}}
            .note{{margin-top:8px;font-size:11px;color:#9ca3af;font-style:italic;}}
        </style></head><body><h3>{cap}</h3><table>{body}</table>{note}</body></html>"""

    @staticmethod
    def xlsx_to_png(source, dpi=170):
        """Randează prima pagină a unui **XLSX generat** exact cum se tipărește, ca PNG.

        XLSX → PDF cu LibreOffice (``soffice --headless``), apoi prima pagină → PNG cu
        ``pdftoppm`` (sau PyMuPDF). Păstrează formatarea din fișier — culori, borduri, format
        de dată și număr, lățimi de coloană, setările de pagină (peisaj, încadrare pe lățime) —
        pe care randarea HTML din `xlsx_to_html` o pierde. Întoarce ``bytes`` PNG sau ``None``
        dacă uneltele lipsesc sau conversia eșuează (apelantul revine la tabelul HTML).
        """
        import base64
        import shutil
        import subprocess
        import tempfile

        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            return None
        if isinstance(source, str) and not os.path.exists(source):
            source = base64.b64decode(source)
        data = source if isinstance(source, (bytes, bytearray)) else open(source, "rb").read()
        with tempfile.TemporaryDirectory() as tmp:
            xlsx_path = os.path.join(tmp, "export.xlsx")
            with open(xlsx_path, "wb") as f:
                f.write(data)
            try:
                subprocess.run(
                    [soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, xlsx_path],
                    check=True,
                    capture_output=True,
                    timeout=120,
                )
            except (subprocess.SubprocessError, OSError):
                _logger.warning("xlsx_to_png: conversia LibreOffice a eșuat, revin la tabelul HTML")
                return None
            pdf_path = os.path.join(tmp, "export.pdf")
            if not os.path.exists(pdf_path):
                return None
            pdftoppm = shutil.which("pdftoppm")
            if pdftoppm:
                try:
                    subprocess.run(
                        [
                            pdftoppm,
                            "-r",
                            str(dpi),
                            "-png",
                            "-f",
                            "1",
                            "-l",
                            "1",
                            "-singlefile",
                            pdf_path,
                            os.path.join(tmp, "page"),
                        ],
                        check=True,
                        capture_output=True,
                        timeout=60,
                    )
                    with open(os.path.join(tmp, "page.png"), "rb") as f:
                        return ScreenshotCase._crop_printed_page(f.read())
                except (subprocess.SubprocessError, OSError) as exc:
                    _logger.debug("xlsx_to_png: pdftoppm a eșuat (%s), încerc PyMuPDF", exc)
            try:
                import fitz  # noqa: PLC0415 — PyMuPDF, opțional

                with fitz.open(pdf_path) as doc:
                    return ScreenshotCase._crop_printed_page(doc[0].get_pixmap(dpi=dpi).tobytes("png"))
            except Exception:  # noqa: BLE001
                return None

    @staticmethod
    def _crop_printed_page(png, footer_band=0.08, padding=16):
        """Decupează pagina tipărită la conținut, fără subsol.

        Numerotarea din subsol („1 / 1", colțul de jos) e tot conținut pentru `_autotrim`,
        care n-ar mai tăia albul dintre tabel și subsol. Căutăm conturul conținutului
        ignorând banda de jos a paginii. Fără Pillow, întoarce imaginea neschimbată.
        """
        try:
            import io  # noqa: PLC0415

            from PIL import Image, ImageOps  # noqa: PLC0415
        except ImportError:
            return png
        img = Image.open(io.BytesIO(png)).convert("RGB")
        w, h = img.size
        body = img.crop((0, 0, w, int(h * (1 - footer_band))))
        bbox = ImageOps.invert(body.convert("L")).point(lambda v: 255 if v > 24 else 0).getbbox()
        if not bbox:
            return png
        left, top, right, bottom = bbox
        cropped = img.crop(
            (max(left - padding, 0), max(top - padding, 0), min(right + padding, w), min(bottom + padding, h))
        )
        out = io.BytesIO()
        cropped.save(out, format="PNG")
        return out.getvalue()

    @classmethod
    def xlsx_shot(cls, source, name, sheet=0, title=None, full=True, **extra):
        """Construiește un element de captură dintr-un **XLSX generat**, randat ca tabel.

        Randează prima pagină a fișierului exact cum se tipărește (`xlsx_to_png`: LibreOffice +
        pdftoppm), cu formatarea lui reală, și întoarce un shot de tip ``html`` care o conține —
        ``capture_screenshots`` îl pozează fără navigare. Fără LibreOffice pe mașină, revine la
        tabelul HTML din ``xlsx_to_html`` (datele reale, fără stilul nativ Excel).

        Utilizare:
            xlsx = self.env["report.xxx"]._get_xlsx(...)        # bytes sau base64
            shots.append(self.xlsx_shot(xlsx, "07_export_xlsx.png", title="Balanță"))
        """
        png = cls.xlsx_to_png(source) if sheet == 0 else None
        if png:
            import base64

            # Pagina tipărită, cu formatarea reală a fișierului; marginile albe se decupează
            # la captură (`trim`).
            html = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'><style>body{margin:0;background:#fff;}"
                "img{display:block;}</style></head><body>"
                f"<img src='data:image/png;base64,{base64.b64encode(png).decode()}'/></body></html>"
            )
        else:
            html = cls.xlsx_to_html(source, sheet=sheet, title=title)
        shot = {"html": html, "name": name, "full": full}
        shot.update(extra)
        return shot

    @staticmethod
    def xml_excerpt(source, max_lines=40, keep_tags=None):
        """Întoarce un **extras formatat** dintr-un XML generat (D300/D390/e-Factura...), pentru fișă.

        XML-ul e text — într-o fișă consultant un extras ``​```xml`` lizibil e mai util decât o
        captură. Acest helper formatează (pretty-print) conținutul și îl truncază la ``max_lines``.
        ``source`` poate fi cale / ``bytes`` / ``str`` (text sau base64). Dacă ``keep_tags`` e dat
        (listă de nume de tag-uri), păstrează doar liniile care conțin acele tag-uri (filtrare grosieră
        pe text, utilă ca să arăți doar antetul și totalurile), inserând ``...`` între blocuri.

        Întoarce un string gata de pus între ``​```xml`` ... ``​``` `` în fișă. Scrie-l manual
        în ``FISA_CONSULTANT.md`` sau loghează-l din test pentru a-l copia.
        """
        import base64
        from xml.dom import minidom

        if isinstance(source, str) and os.path.exists(source):
            raw = open(source, "rb").read()
        elif isinstance(source, (bytes, bytearray)):
            raw = bytes(source)
        else:
            text = source
            try:  # poate fi base64
                if "<" not in text[:64]:
                    raw = base64.b64decode(text)
                else:
                    raw = text.encode("utf-8")
            except Exception:  # noqa: BLE001
                raw = text.encode("utf-8")

        try:
            pretty = minidom.parseString(raw).toprettyxml(indent="  ")
            lines = [ln for ln in pretty.splitlines() if ln.strip()]
        except Exception:  # noqa: BLE001 - XML invalid → întoarce textul brut truncat
            lines = raw.decode("utf-8", "replace").splitlines()

        if keep_tags:
            kept, prev_kept = [], True
            for ln in lines:
                if any(t in ln for t in keep_tags):
                    kept.append(ln)
                    prev_kept = True
                elif prev_kept:
                    kept.append("  ...")
                    prev_kept = False
            lines = kept

        if len(lines) > max_lines:
            lines = lines[:max_lines] + [f"  <!-- ... truncat la {max_lines} linii ... -->"]
        return "\n".join(lines)

    @classmethod
    def prepare_demo_company(cls, company_xmlid="base.demo_company_ro"):
        """Pregătește capturile pe **compania demo** a localizării (cu date demo populate).

        Setează compania demo ca firmă activă pentru admin și acordă drepturile contabile.
        Util pentru module cu raport/flux unde datele demo (facturi etc.) populează ecranele,
        evitând seeding-ul manual. Returnează compania demo (sau env.company dacă lipsește).
        """
        env = cls.env
        company = env.ref(company_xmlid, raise_if_not_found=False)
        if not company:
            return env.company
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [(4, company.id)], "company_id": company.id})
        for xmlid in ("account.group_account_readonly", "account.group_account_user", "account.group_account_manager"):
            grp = env.ref(xmlid, raise_if_not_found=False)
            if grp:
                admin.group_ids = [(4, grp.id)]
        env.flush_all()
        cls.activate_ro_lang()
        cls.force_light_theme()
        cls.align_website_company(company)
        return company

    def screenshots_dir(self, lang=DEFAULT_LANG):
        assert self.screenshots_module, "Setați atributul `screenshots_module` pe clasa de test."
        path = get_module_path(self.screenshots_module)
        description = os.path.join(path, "static", "description")
        if lang != DEFAULT_LANG:
            # Capturile în altă limbă (``en/``) sunt pentru readme/USAGE.md, publicat pe Apps
            # Store, deci stau mereu sub static/description/, chiar și la modulele nemigrate.
            return os.path.join(description, lang.split("_")[0])
        # Convenția nouă: capturile stau în static/description/, de unde le servește și
        # Apps Store. Modulele din suitele încă nemigrate păstrează readme/screenshots/.
        legacy = os.path.join(path, "readme", "screenshots")
        if os.path.isdir(legacy):
            return legacy
        return description

    def capture_screenshots(
        self, shots, login="admin", viewport=(1920, 950), locale=None, hide_systray=False, lang=DEFAULT_LANG
    ):
        """Generează capturile descrise în ``shots``.

        Fiecare element din ``shots`` este un dict cu:
          - ``url`` (str): fragmentul de după ``/web#`` (ex. ``action=12&view_type=list``); SAU
          - ``path`` (str): cale absolută pe server (ex. ``/report/html/<report>/<id>`` pentru rapoarte —
            vezi ``report_shot`` pentru randarea HTML a unui PDF tipăribil); SAU
          - ``html`` (str): conținut HTML inline pozat direct, fără navigare (ex. tabel dintr-un XLSX
            generat — vezi ``xlsx_shot``); ``wait``/``url``/``path`` se ignoră pentru acest tip;
          - ``name`` (str, obligatoriu): numele fișierului ``.png``;
          - ``full`` (bool): captură pe toată pagina (implicit False);
          - ``wait`` (str): selector CSS de așteptat (implicit form sau listă);
          - ``timeout`` (int): ms de așteptare pentru ``wait``/``wait_after`` (implicit 20000); mărește-l
            pentru ecrane grele (ex. Setări într-o bază cu multe module);
          - ``hover`` (str): selector CSS peste care se trece cu mouse-ul înainte de click/captură
            (ex. un card kanban al cărui meniu ⋮ e vizibil doar la hover);
          - ``click_btn`` (str): selector CSS pe care se dă click înainte de captură (ex. smart button);
          - ``click_tab`` (str): textul unui tab de notebook pe care se dă click;
          - ``unfold_report`` (bool): desfășoară toate liniile pliabile dintr-un account.report
            (click pe fiecare caret colapsat) înainte de captură — util pentru rapoarte cu detalii;
          - ``eval`` (str): cod JS rulat în pagină înainte de captură (ex. desfășurări custom);
          - ``hide_fields`` (list[str]): nume tehnice de câmpuri (atributul ``name`` din formular)
            de ascuns cu eticheta lor — util pentru câmpuri injectate de un modul frate pe un
            model comun (ex. ``account.journal``), irelevante pentru fișa curentă;
          - ``highlight`` (str | list[str]): selector(e) CSS / Playwright (``:has-text`` permis) pentru
            butoanele/câmpurile implicate în pas — primesc un contur portocaliu Odoo + halou și o
            bulină numerotată ①②③ (un număr per selector, în ordinea din listă). Util ca fișa să
            indice exact unde apasă/completează operatorul;
          - ``settle`` (int): pauză în ms înainte de captură (implicit 1500).

        ``lang`` (implicit ``"ro_RO"``) e limba interfeței pe capturi: se setează pe utilizator
        înainte de autentificare, dă locale-ul browserului (dacă ``locale`` nu e dat) și limba
        rapoartelor din ``report_shot``. Capturile în altă limbă decât RO se scriu în subfolderul
        ei (``static/description/en/`` pentru ``en_US``), cu aceleași nume ca în fișă. Orice
        valoare din shot poate fi dependentă de limbă, ca dict ``{"ro_RO": ..., "en_US": ...}``
        (ex. ``"highlight": {"ro_RO": "button:has-text('Confirmă')", "en_US":
        "button:has-text('Confirm')"}``) — preferați însă selectoarele după ``name``, valabile
        în orice limbă.

        ``hide_systray=True`` ascunde bara de iconuri din dreapta-sus (AI, notificări, Studio,
        meniul de debug) pe toate capturile — zgomot inutil într-un manual de client. Injectat
        ca ``<style>``, deci rezistă la re-randările OWL, spre deosebire de ``remove()`` pe nod.

        Returnează lista căilor scrise.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright nu este instalat (uv pip install playwright)")

        out = self.screenshots_dir(lang)
        os.makedirs(out, exist_ok=True)
        base = self.base_url()
        locale = locale or lang.replace("_", "-")

        # Pe o bază fără date demo, ``res.users.tour_enabled`` (web_tour, compute stocat) e True
        # pentru admin, iar indicatorul turului de onboarding (picătura mov) apare în capturi
        # peste butonul „Nou". Îl oprim pentru utilizatorul care face capturile.
        user = self.env["res.users"].sudo().search([("login", "=", login)], limit=1)
        if user and "tour_enabled" in user._fields:
            user.tour_enabled = False
        # limba interfeței o dă utilizatorul (contextul sesiunii), nu locale-ul browserului
        if user and user.lang != lang:
            self.activate_lang(lang, user=user)

        # autentificăm sesiunea și o transmitem browserului prin cookie (sărim formularul de login,
        # care expiră pe serverul de test); all_requests permite serverului să servească browserul.
        self.authenticate(login, login)
        sid = self.session.sid

        written = []
        with self.allow_requests(all_requests=True), _unlimited_address_space(), sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            ctx = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]}, locale=locale)
            ctx.add_cookies([{"name": "session_id", "value": sid, "url": base}])
            page = ctx.new_page()
            # Erorile JS ale paginii se colectează și se raportează la eșec: când clientul
            # web crapă în timp ce construiește un ecran, `wait_for_selector` întoarce doar
            # „Timeout exceeded", fără nicio urmă despre cauză, iar în log-ul serverului
            # cererea de dinainte (ex. `get_views`) apare cu 200 — deci pare că totul e bine.
            js_errors = []
            page.on("pageerror", lambda e: js_errors.append(f"pageerror: {e}"))
            page.on(
                "console",
                lambda m: js_errors.append(f"console.error: {m.text}") if m.type == "error" else None,
            )
            try:
                shot_name = "?"
                for s in shots:
                    s = {key: _for_lang(value, lang) for key, value in s.items()}
                    if s.get("report_path"):
                        context = dict(s.get("report_context") or {}, lang=lang)
                        s["path"] = s["report_path"] + "?context=" + quote(json.dumps(context))
                    shot_name = s.get("name", "?")
                    if s.get("html") is not None:
                        # Shot din HTML inline (ex. tabel randat dintr-un XLSX generat) — nu navigăm,
                        # injectăm conținutul direct și pozăm. Vezi ``xlsx_shot``.
                        page.set_content(s["html"], wait_until="domcontentloaded")
                    else:
                        target = f"{base}{s['path']}" if s.get("path") else f"{base}/web#{s['url']}"
                        resp = page.goto(target, wait_until="domcontentloaded")
                        # o eroare de server (ex. 500 la randarea unui raport) produce tot o pagină
                        # HTML care trece de ``wait="body"`` — fără verificarea asta captura ar
                        # salva pagina de eroare peste imaginea bună din fișă
                        if resp is not None and resp.status >= 400:
                            raise AssertionError(f"HTTP {resp.status} la {s.get('path') or s['url']}")
                        # ``timeout`` (ms) opțional per-shot: ecranele grele (ex. Setări într-o bază
                        # cu multe module) pot depăși cele 20s implicite la prima randare a bundle-ului.
                        wait_timeout = s.get("timeout", 20000)
                        page.wait_for_selector(s.get("wait", DEFAULT_READY), timeout=wait_timeout)
                        if hide_systray:
                            # tooltipul rămas de la un shot anterior apare ca o casetă neagră
                            # peste conținut, așa că îl ascundem odată cu bara de iconuri
                            page.add_style_tag(content=".o_menu_systray, .o-tooltip, .tooltip{display:none !important}")
                    if s.get("hover"):
                        # elementele vizibile doar la hover (ex. meniul ⋮ al cardurilor kanban);
                        # force=True: cardurile cu grafice animate nu trec testul de stabilitate
                        page.locator(s["hover"]).first.hover(timeout=8000, force=True)
                        # hover-ul sintetic nu declanșează mereu CSS :hover — elementele care
                        # apar doar la hover rămân visibility:hidden și nu primesc click-uri;
                        # le forțăm vizibile ca pasul click_btn să le poată acționa
                        page.evaluate(
                            "document.querySelectorAll('.o_dropdown_kanban')"
                            ".forEach(e => { e.style.visibility = 'visible'; })"
                        )
                    if s.get("click_btn"):
                        page.locator(s["click_btn"]).first.click(timeout=8000, force=True)
                        # implicit așteptăm un formular; pentru dropdown/meniu folosiți ``wait_after``
                        page.wait_for_selector(s.get("wait_after", ".o_form_view"), timeout=s.get("timeout", 20000))
                    if s.get("click_tab"):
                        # Capturile se fac cu interfața în RO sau EN, deci tab-ul cerut într-o
                        # limbă nu se găsește în cealaltă: încercăm și eticheta tradusă, altfel
                        # shot-ul ar rămâne tăcut pe primul tab (ex. factura fără liniile Dr/Cr).
                        tab_en = {ro: en for en, ro in TAB_LABELS_RO.items()}
                        for label in (s["click_tab"], TAB_LABELS_RO.get(s["click_tab"]), tab_en.get(s["click_tab"])):
                            if not label:
                                continue
                            try:
                                page.click(f"a.nav-link:has-text('{label}')", timeout=4000)
                                break
                            except Exception:  # noqa: BLE001 - tab opțional
                                continue
                    if s.get("unfold_report"):
                        # Desfășoară liniile pliabile dintr-un account.report, **secvențial** (câte
                        # unul, așteptând RPC-ul de încărcare a subliniilor). Click-urile concurente
                        # ar insera subliniile la index greșit (toate sub primul părinte).
                        for _ in range(60):  # plafon de siguranță
                            caret = page.query_selector('td.line_name button[data-id="btn_foldable"] i.fa-caret-right')
                            if not caret:
                                break
                            caret.evaluate("i => i.closest('td.line_name').click()")
                            try:
                                page.wait_for_load_state("networkidle", timeout=5000)
                            except Exception:  # noqa: BLE001 - fallback pauză fixă
                                page.wait_for_timeout(600)
                    if s.get("hide_fields"):
                        # ascunde câmpul și eticheta lui. Eticheta e potrivită independent de
                        # poziția în DOM, prin atributul 'for' (= numele câmpului în InnerGroup
                        # Odoo). Grupul e un CSS Grid ('.o_inner_group.grid'): 'display: none'
                        # pe o singură celulă scoate acea celulă din flux și RE-ALOCĂ restul
                        # celulelor în grid, amestecând etichete cu valorile altor câmpuri —
                        # de aceea folosim 'visibility: hidden' (păstrează locul în grid, fără
                        # realocare), acceptând spațiul gol rămas.
                        page.evaluate(
                            """(names) => {
                                const hideCell = (el) => {
                                    (el.closest('.o_cell') || el).style.visibility = 'hidden';
                                };
                                // atributul 'for' e 'fieldName_N' (sufix unic Owl), nu fieldName exact
                                document.querySelectorAll('label.o_form_label').forEach((lbl) => {
                                    const forAttr = lbl.getAttribute('for') || '';
                                    if (names.some((n) => forAttr === n || forAttr.startsWith(n + '_'))) {
                                        hideCell(lbl);
                                    }
                                });
                                names.forEach((name) => {
                                    document.querySelectorAll(`[name='${name}']`).forEach(hideCell);
                                });
                            }""",
                            s["hide_fields"],
                        )
                    if s.get("eval"):
                        try:
                            page.evaluate(s["eval"])
                            page.wait_for_timeout(s.get("eval_wait", 800))
                        except Exception:  # noqa: BLE001 - JS opțional
                            _logger.debug("Screenshots: JS opțional", exc_info=True)
                    if s.get("hide_chatter", True):
                        try:
                            page.evaluate(
                                "() => document.querySelectorAll("
                                "'.o-mail-Chatter, .o-mail-ChatterContainer, "
                                ".o_FormRenderer_chatterContainer, .o-mail-Form-chatter, .o_chatter')"
                                ".forEach(e => { e.style.display = 'none'; })"
                            )
                        except Exception:  # noqa: BLE001 - chatter opțional
                            _logger.debug("Screenshots: chatter opțional", exc_info=True)
                    if s.get("highlight"):
                        self._apply_highlight(page, s["highlight"])
                    if not s.get("hover"):
                        # cursorul rămas peste o celulă deschide tooltipul ei, care apare
                        # ca o casetă neagră peste conținut în captură
                        page.mouse.move(0, 0)
                    page.wait_for_timeout(s.get("settle", 1500))
                    dest = os.path.join(out, s["name"])
                    page.screenshot(path=dest, full_page=s.get("full", False))
                    if s.get("trim", True):
                        self._autotrim(dest)
                    if os.sep + os.path.join("static", "description") + os.sep in dest:
                        self._fit_for_apps(dest)
                    written.append(dest)
            except Exception as exc:  # noqa: BLE001 - re-ridicăm, doar adăugăm diagnosticul
                # Numele shot-ului curent + erorile JS strânse: fără ele, un ecran care crapă
                # în client se raportează ca simplu timeout pe un selector, fără să spună
                # nici măcar la care captură s-a oprit.
                detalii = "\n".join(f"  - {e}" for e in dict.fromkeys(js_errors)) or "  (niciuna)"
                raise AssertionError(f"Captura '{shot_name}' a eșuat: {exc}\nErori JS în pagină:\n{detalii}") from exc
            finally:
                browser.close()
        return written

    #: JS aplicat pe fiecare element evidențiat: contur portocaliu Odoo + halou translucid și,
    #: dacă ``num`` nu e null, o bulină numerotată în colțul stânga-sus. ``num`` e dat o singură
    #: dată per selector (pe primul element potrivit), ca numerotarea să urmeze pașii, nu liniile.
    _HIGHLIGHT_JS = """
        (el, num) => {
            el.style.outline = '3px solid #f0820e';
            el.style.outlineOffset = '2px';
            el.style.borderRadius = '5px';
            el.style.boxShadow = '0 0 0 5px rgba(240,130,14,.20)';
            if (num !== null) {
                if (getComputedStyle(el).position === 'static') { el.style.position = 'relative'; }
                const b = document.createElement('div');
                b.textContent = num;
                b.setAttribute('data-fise-badge', '1');
                b.style.cssText = 'position:absolute;top:-13px;left:-13px;width:24px;height:24px;'
                    + 'background:#f0820e;color:#fff;border-radius:50%;display:flex;align-items:center;'
                    + 'justify-content:center;font-weight:700;font-size:13px;'
                    + 'box-shadow:0 1px 3px rgba(0,0,0,.4);z-index:50;pointer-events:none;';
                el.appendChild(b);
            }
        }
    """

    @classmethod
    def _apply_highlight(cls, page, highlight):
        """Evidențiază butoanele/câmpurile unui pas: contur portocaliu + halou + badge numerotat.

        ``highlight`` e un selector (str) sau o listă de selectoare. Fiecare selector primește un
        număr (ordinea din listă); dacă prinde mai multe elemente (ex. o coloană pe toate liniile),
        toate capătă contur, dar badge-ul apare doar pe primul. Acceptă selectoare Playwright
        (``button:has-text('Confirmă')``) pentru că folosim ``page.locator`` element-cu-element,
        nu ``querySelectorAll``. Defensiv: un selector inexistent e ignorat în liniște.
        """
        selectors = [highlight] if isinstance(highlight, str) else list(highlight)
        for num, sel in enumerate(selectors, start=1):
            try:
                loc = page.locator(sel)
                count = loc.count()
            except Exception:  # noqa: BLE001 - selector invalid → sărim peste
                continue
            for j in range(count):
                try:
                    loc.nth(j).evaluate(cls._HIGHLIGHT_JS, num if j == 0 else None)
                except Exception:  # noqa: BLE001 - element dispărut între timp
                    _logger.debug("Screenshots: element dispărut între timp", exc_info=True)

    #: lățimea maximă a capturii: ca pe Odoo Apps Store (peste ~1250 px umple toată pagina)
    APPS_MAX_WIDTH = 1245

    @classmethod
    def _fit_for_apps(cls, path):
        """Aduce captura la cel mult ``APPS_MAX_WIDTH`` px lățime, cu paletă de 256 de culori.

        Capturile stau în ``static/description/`` și se publică pe Apps Store direct din
        USAGE.md; la 1920 px și pe 24 de biți ar fi de ~3 ori mai mari. No-op fără Pillow.
        """
        try:
            from PIL import Image  # noqa: PLC0415
        except ImportError:
            return
        try:
            img = Image.open(path)
        except Exception:  # noqa: BLE001
            return
        if img.width > cls.APPS_MAX_WIDTH:
            img = img.convert("RGB")
            img = img.resize((cls.APPS_MAX_WIDTH, round(img.height * cls.APPS_MAX_WIDTH / img.width)), Image.LANCZOS)
        elif img.mode == "P":
            return
        # Image.Quantize / Image.Dither exist since Pillow 9.1; Odoo 19 pins 9.0.1 on Python 3.10,
        # where the same values are module constants (Image.MEDIANCUT, Image.NONE).
        quantize = getattr(Image, "Quantize", Image)
        dither = getattr(Image, "Dither", Image)
        img.convert("RGB").quantize(256, method=quantize.MEDIANCUT, dither=dither.NONE).save(path, optimize=True)

    @staticmethod
    def _autotrim(path, padding=10, tol=24):
        """Decupează marginile uniforme (fundalul) — elimină spațiul gol (ex. liste scurte).

        Spre deosebire de o estimare cu o singură culoare de fundal, folosește **mai multe
        tonuri de fundal** eșantionate de pe marginea de jos (colțuri + mijloc). Astfel
        gestionează corect ecranele cu fundal neuniform — de pildă un raport scurt (gri
        deschis) lângă panoul de chatter (alb): un singur ``bg`` din colț ar fi tratat
        celălalt fundal ca „conținut" și nu ar mai tăia nimic.

        Un pixel e considerat conținut dacă diferă (distanță Manhattan > ``tol``) de **toate**
        tonurile de fundal candidate. Conturul (navbar full-width sus) rămâne; se taie mai
        ales spațiul gol de jos/lateral. No-op dacă nu există margine de tăiat sau dacă
        Pillow/NumPy lipsesc.
        """
        try:
            from PIL import Image, ImageChops  # noqa: PLC0415
        except ImportError:
            return
        try:
            img = Image.open(path).convert("RGB")
        except Exception:  # noqa: BLE001
            return
        w, h = img.size

        # Tonuri de fundal candidate: marginea de jos (sigur goală), stânga→dreapta,
        # ca să prindem și un eventual al doilea fundal (ex. panoul de chatter, alb).
        sample_xs = {2, w // 4, w // 2, (3 * w) // 4, w - 3}
        bg_colors = {img.getpixel((min(max(x, 0), w - 1), h - 2)) for x in sample_xs}

        try:
            import numpy as np  # noqa: PLC0415

            arr = np.asarray(img, dtype=np.int16)
            is_content = np.ones((h, w), dtype=bool)
            for bg in bg_colors:
                dist = np.abs(arr - np.array(bg, dtype=np.int16)).sum(axis=2)
                is_content &= dist > tol
            rows = np.where(is_content.any(axis=1))[0]
            cols = np.where(is_content.any(axis=0))[0]
            if not len(rows) or not len(cols):
                return
            top, bottom = int(rows[0]), int(rows[-1]) + 1
            left, right = int(cols[0]), int(cols[-1]) + 1
        except ImportError:
            # Fallback fără NumPy: estimare clasică cu o singură culoare (colț dreapta-jos).
            bg = Image.new("RGB", img.size, img.getpixel((w - 2, h - 2)))
            bbox = ImageChops.difference(img, bg).getbbox()
            if not bbox:
                return
            left, top, right, bottom = bbox

        left = max(0, left - padding)
        top = max(0, top - padding)
        right = min(w, right + padding)
        bottom = min(h, bottom + padding)
        if right - left < w or bottom - top < h:
            img.crop((left, top, right, bottom)).save(path)
