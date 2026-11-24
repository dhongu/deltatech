# © 2026 Terrabit Solutions
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant „Exemple de căutare scrise în caseta de căutare" —
# generate în timpul testelor, în limba RO.
#
# Seedează o pagină de website cu o casetă de căutare care are lista de exemple
# (o_searchbar_typing) și fotografiază: vizualizarea paginii (backend), placeholderul care
# scrie un exemplu și placeholderul inițial, revenit la click în casetă. Pentru Apps Store,
# GIF-ul demo (static/description/en/demo.gif) rulează pe o pagină în engleză, cu exemplele
# tastate în ritmul normal.
#
# Rulare:
#   .venv/bin/python odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_website_searchbar_typing,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo.tests import HttpCase, tagged

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

PAGE_URL = "/ghiduri-utilizare"

# Exemplul rămâne scris pe ecran (hold-delay mare), ca poza să nu depindă de momentul capturii.
PAGE_ARCH = """
<t t-name="deltatech_website_searchbar_typing.screenshots_page">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">
            <section class="container py-5">
                <h1 class="mb-4">Ghiduri de utilizare</h1>
                <div class="col-lg-8">
                    <t t-call="website.website_search_box_input"
                       search_type.f="all" action.f="/website/search"
                       placeholder.f="Caută în ghidurile de utilizare">
                        <ul class="o_searchbar_typing d-none" aria-hidden="true"
                            data-start-delay="300" data-type-delay="40" data-hold-delay="600000">
                            <li class="o_searchbar_typing_prefix">ex.:</li>
                            <li>import extras de cont</li>
                            <li>factură de stornare</li>
                            <li>e-Factura</li>
                        </ul>
                    </t>
                </div>
            </section>
        </div>
    </t>
</t>
"""


GIF_URL = "/help-center"

# un cadru al GIF-ului la fiecare TICK_MS, în timp real
TICK_MS = 250
TICK_JS = f"new Promise((resolve) => setTimeout(resolve, {TICK_MS}))"

# Pagina GIF-ului: ritm apropiat de cel implicit, ca exemplele să se scrie și să se șteargă.
GIF_PAGE_ARCH = """
<t t-name="deltatech_website_searchbar_typing.gif_page">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">
            <section class="container py-5">
                <div class="col-lg-8 mx-auto">
                    <h1 class="mb-2">Search the help center</h1>
                    <p class="mb-3">User guides, articles and answers to frequent questions</p>
                    <t t-call="website.website_search_box_input"
                       search_type.f="all" action.f="/website/search"
                       placeholder.f="Search the help center...">
                        <ul class="o_searchbar_typing d-none" aria-hidden="true"
                            data-start-delay="600" data-type-delay="80" data-hold-delay="1400">
                            <li class="o_searchbar_typing_prefix">e.g.</li>
                            <li>bank statement import</li>
                            <li>credit note</li>
                            <li>e-Invoice</li>
                        </ul>
                    </t>
                </div>
            </section>
        </div>
    </t>
</t>
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSearchbarTypingScreenshots(ScreenshotCase or HttpCase):
    screenshots_module = "deltatech_website_searchbar_typing"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.activate_ro_lang()
        cls.force_light_theme()
        env = cls.env
        website = env["website"].search([], limit=1)
        lang_ro = env["res.lang"].search([("code", "=", "ro_RO")], limit=1)
        if lang_ro:
            website.write({"language_ids": [(4, lang_ro.id)], "default_lang_id": lang_ro.id})
        page = env["website.page"].create(
            {
                "name": "Ghiduri de utilizare",
                "url": PAGE_URL,
                "type": "qweb",
                "arch": PAGE_ARCH,
                "key": "deltatech_website_searchbar_typing.screenshots_page",
                "website_id": website.id,
                "is_published": True,
            }
        )
        cls.page_view = page.view_id
        env["website.page"].create(
            {
                "name": "Help Center",
                "url": GIF_URL,
                "type": "qweb",
                "arch": GIF_PAGE_ARCH,
                "key": "deltatech_website_searchbar_typing.gif_page",
                "website_id": website.id,
                "is_published": True,
            }
        )
        # vizitatorul: un utilizator portal (capture_screenshots se autentifică cu parola = login)
        cls.visitor = env["res.users"].create(
            {
                "name": "Vizitator Demo",
                "login": "vizitator@demo.ro",
                "password": "vizitator@demo.ro",
                "lang": "ro_RO",
                "group_ids": [(6, 0, [env.ref("base.group_portal").id])],
            }
        )

    def test_capture_fise(self):
        # 1. Lista de exemple în vizualizarea paginii (backend, mod dezvoltator)
        self.capture_screenshots(
            [
                {
                    "url": f"id={self.page_view.id}&model=ir.ui.view&view_type=form&debug=1",
                    "name": "01_lista_exemple.png",
                    "wait": ".o_form_view",
                    "click_tab": "Architecture",
                    "settle": 2500,
                },
            ],
            viewport=(1500, 1000),
            hide_systray=True,
        )
        input_sel = "#wrap .o_searchbar_form .search-query"
        self.capture_screenshots(
            [
                # 2. Placeholderul scrie primul exemplu
                {
                    "path": PAGE_URL,
                    "name": "02_placeholder_exemplu.png",
                    "wait": f"{input_sel}[placeholder^='ex.: ']",
                    "highlight": input_sel,
                    "settle": 3000,
                },
                # 3. La click în casetă revine placeholderul inițial
                {
                    "path": PAGE_URL,
                    "name": "03_focus_placeholder_initial.png",
                    "wait": f"{input_sel}[placeholder^='ex.: ']",
                    "click_btn": input_sel,
                    "wait_after": f"{input_sel}[placeholder='Caută în ghidurile de utilizare']",
                    "highlight": input_sel,
                    "settle": 1500,
                },
            ],
            login=self.visitor.login,
            viewport=(1300, 300),
        )

    def _gif_steps(self):
        """Demo-ul de pe pagina Apps: placeholderul tastează exemple, iar click-ul îl oprește."""
        input_sel = "#wrap .o_searchbar_form .search-query"

        def ticks(count):
            # `hold` doar prelungește cadrul; animația merge în timp real, deci așteptăm în pagină
            # între cadre, ca literele tastate și șterse să intre în GIF
            return [{"eval": TICK_JS, "hold": TICK_MS} for _i in range(count)]

        # website-ul are româna implicită: pagina în engleză se deschide cu prefixul limbii
        return [
            {"path": f"/en{GIF_URL}", "wait": f"{input_sel}[placeholder^='e.g. ']"},
            # cursorul stă pe buton, ca să nu acopere textul tastat
            {"caption": "The search box types example searches", "move": "#wrap .o_searchbar_form button"},
            *ticks(14),
            {"caption": "Each example is erased, the next one follows"},
            *ticks(22),
            {
                "caption": "A click in the box stops the animation",
                "click": input_sel,
                "wait_after": f"{input_sel}[placeholder='Search the help center...']",
                "hold": 2500,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        # suita deltatech are pagina Apps doar în engleză
        self.capture_gif(self._gif_steps(), login=self.visitor.login, lang="en_US")
