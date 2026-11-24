# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# GIF-ul demo pentru pagina Apps Store (static/description/en/demo.gif): un contact nou,
# persoană fizică, primește CNP-ul, iar data nașterii și sexul se completează din el.
#
# În Odoo 20 comutatorul persoană/firmă din 19.0 a dispărut: `is_company` e calculat, iar acțiunea
# Contacts pornește un contact nou cu `default_is_company`. Persoana se leagă deci de firmă prin
# „Company Employer” (parent_id), după care fila „Personal Data” apare.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_contact,deltatech_doc_screenshots \
#       --test-tags=/deltatech_contact:TestContactScreenshots.test_capture_gif --stop-after-init
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# CNP-ul unei persoane noi: 2 = femeie născută în 1900–1999, 900315 = 15 martie 1990
NEW_CNP = "2900315400018"

# fila adăugată de modul nu are atributul name, deci o căutăm după etichetă
PERSONAL_TAB = {
    "ro_RO": ".o_notebook .nav-link:has-text('Date personale')",
    "en_US": ".o_notebook .nav-link:has-text('Personal Data')",
}


@tagged("-at_install", "post_install", "fise_screenshots")
class TestContactScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_contact"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        # date fictive; codul fiscal face din partener o firmă
        cls.env["res.partner"].create(
            {
                "name": "Agro Prod SRL",
                "vat": "RO14399840",
                "street": "Str. Morii nr. 5",
                "city": "Ploiești",
                "country_id": cls.env.ref("base.ro").id,
            }
        )
        cls.action = cls.env.ref("contacts.action_contacts").id

    def _gif_steps(self):
        """Demo-ul de pe pagina Apps: CNP-ul tastat completează singur data nașterii și sexul."""
        menu = self.env.ref("contacts.menu_contacts").id
        return [
            {"goto": f"action={self.action}&menu_id={menu}&model=res.partner&view_type=form"},
            {
                "caption": {
                    "ro_RO": "Un contact nou, persoană fizică",
                    "en_US": "A new contact, an individual",
                },
                "type": "Maria Ionescu",
                "into": "name",
                "hold": 400,
            },
            {
                "caption": {
                    "ro_RO": "Persoana lucrează la o firmă",
                    "en_US": "The person works for a company",
                },
                "type": "Agro Prod",
                "into": "parent_id",
            },
            # `wait` fără `goto` așteaptă înainte de click: lista de sugestii a many2one-ului
            {"wait": ".o-autocomplete--dropdown-menu", "click": ".o-autocomplete--dropdown-item:first-child"},
            {
                "caption": {
                    "ro_RO": "Datele de identitate au fila lor",
                    "en_US": "Identity data has its own tab",
                },
                "click": PERSONAL_TAB,
            },
            {
                "caption": {"ro_RO": "Se introduce doar CNP-ul", "en_US": "Only the CNP is typed in"},
                "type": NEW_CNP,
                "into": "cnp",
            },
            {
                "caption": {
                    "ro_RO": "Data nașterii și sexul se completează din CNP",
                    "en_US": "Birthdate and gender are filled from the CNP",
                },
                # click pe fila deja activă: CNP-ul pierde focusul (onchange), fără să deschidă
                # calendarul câmpului următor, cum ar face Tab
                "click": PERSONAL_TAB,
                "hold": 2800,
            },
            {
                "caption": {
                    "ro_RO": "La salvare, CNP-ul e verificat",
                    "en_US": "On save, the CNP is checked",
                },
                "click": ".o_form_button_save",
                "wait_after": ".o_form_saved",
                "hold": 2200,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        # suita deltatech are pagina Apps doar în engleză
        self.capture_gif(self._gif_steps(), lang="en_US")
