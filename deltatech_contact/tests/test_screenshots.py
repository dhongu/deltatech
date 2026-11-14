# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Date personale pe contacte (CNP, carte de identitate)", în RO
# (fișa) și EN (readme/USAGE.md).
#
# Seedează firma Agro Prod SRL cu persoana de contact Andrei Popescu (CNP, carte de identitate,
# mijloc de transport), o adresă de livrare și una de facturare, pentru filtrele noi.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_contact,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import json
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# fila adăugată de modul nu are atributul name, deci o căutăm după etichetă
PERSONAL_TAB = {"ro_RO": "Date personale", "en_US": "Personal Data"}

# CNP-ul unei persoane noi: 2 = femeie născută în 1900–1999, 900315 = 15 martie 1990
NEW_CNP = "2900315400018"

# Pașii unui ecran, rulați în pagină: fila se randează abia după click, deci și câmpurile ei.
# Câmpurile se scriu ca la tastare: OWL preia valoarea la evenimentul change.
STEPS_JS = """(async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const steps = %s;
    for (const [kind, arg, value] of steps) {
        if (kind === "click") {
            document.querySelector(arg).click();
        } else if (kind === "tab") {
            [...document.querySelectorAll("a.nav-link")].find((a) => a.textContent.trim() === arg).click();
        } else if (kind === "style") {
            const style = document.createElement("style");
            style.textContent = arg;
            document.head.appendChild(style);
        } else if (kind === "type") {
            const input = document.querySelector(`.o_form_view div[name='${arg}'] input`);
            input.focus();
            input.value = value;
            input.dispatchEvent(new Event("input", {bubbles: true}));
            input.dispatchEvent(new Event("change", {bubbles: true}));
        }
        await sleep(900);
    }
})()"""


# bulina evidențierii stă pe colțul câmpului: fără spațiu, acoperă prima cifră a valorii
# și e tăiată de celulele grupului, dacă nu le lăsăm să depășească
PAD_FIELDS = (
    ".tab-pane.active .o_field_widget input:not([type=radio]), .tab-pane.active .o_field_widget select,"
    " .tab-pane.active .o_field_date button { padding-left: 22px !important; }"
    " .o_form_sheet, .o_notebook, .tab-content, .tab-pane, .o_group, .o_inner_group, .o_cell, .o_row"
    " { overflow: visible !important; }"
)
# rândurile meniului de filtre sunt lipite, iar cadrele evidențierilor s-ar suprapune
SPACE_FILTERS = (
    ".o_search_bar_menu .o_menu_item { margin: 8px 0 8px 12px !important; }"
    " .o_search_bar_menu, .o_search_bar_menu * { overflow: visible !important; }"
)


def steps(*items):
    """JS-ul pașilor, pe limbi: eticheta filei diferă între RO și EN."""
    return {
        lang: STEPS_JS % json.dumps([[k, a[lang] if isinstance(a, dict) else a, *v] for k, a, *v in items])
        for lang in ("ro_RO", "en_US")
    }


@tagged("-at_install", "post_install", "fise_screenshots")
class TestContactScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_contact"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        env = cls.env
        partner = env["res.partner"]
        cls.company_partner = partner.create(
            {
                "name": "Agro Prod SRL",
                "is_company": True,
                "vat": "RO14399840",
                "street": "Str. Morii nr. 5",
                "city": "Ploiești",
                "country_id": env.ref("base.ro").id,
                "lang": "ro_RO",
            }
        )
        cls.person = partner.create(
            {
                "name": "Andrei Popescu",
                "parent_id": cls.company_partner.id,
                "function": "Șofer",
                "phone": "0722 111 222",
                "cnp": "1850101123451",
                "birthdate": "1985-01-01",
                "gender": "male",
                "id_series": "PH",
                "id_nr": "123456",
                "id_issued_by": "SPCLEP Ploiești",
                "id_issued_at": "2020-05-10",
                "mean_transp": "PH-10-APR",
                "lang": "ro_RO",
            }
        )
        partner.create(
            {
                "name": "Depozit Ploiești",
                "parent_id": cls.company_partner.id,
                "type": "delivery",
                "street": "Str. Depozitelor nr. 2",
                "city": "Ploiești",
            }
        )
        partner.create(
            {
                "name": "Contabilitate",
                "parent_id": cls.company_partner.id,
                "type": "invoice",
                "email": "contabilitate@example.ro",
            }
        )
        cls.action = env.ref("contacts.action_contacts").id

    def _form_url(self, record=None):
        rec = f"&id={record.id}" if record else ""
        return f"action={self.action}{rec}&model=res.partner&view_type=form"

    def _shots(self):
        # 02 la sfârșit: contactul nou se salvează la plecarea de pe pagină și ar apărea în lista de la 05
        return [
            {
                "url": self._form_url(self.person),
                "name": "01_contact_date_personale.png",
                "wait": ".o_form_view div[name='parent_id']",
                "eval": steps(("tab", PERSONAL_TAB), ("style", PAD_FIELDS)),
                "highlight": [
                    "div[name='id_series']",
                    "div[name='id_issued_by']",
                    "div[name='cnp']",
                    "div[name='birthdate']",
                    "div[name='gender']",
                ],
            },
            {
                "url": self._form_url(self.person),
                "name": "03_cnp_invalid.png",
                "wait": ".o_form_view div[name='parent_id']",
                "eval": steps(("tab", PERSONAL_TAB), ("type", "cnp", "1850101"), ("click", ".o_form_button_save")),
                "eval_wait": 2000,
                "highlight": [".modal .modal-content"],
            },
            {
                "url": self._form_url(self.person),
                "name": "04_mijloc_transport.png",
                "wait": ".o_form_view div[name='parent_id']",
                "eval": steps(("click", "a.nav-link[name='sales_purchases']"), ("style", PAD_FIELDS)),
                "highlight": ["div[name='mean_transp']"],
            },
            {
                "url": f"action={self.action}&model=res.partner&view_type=list",
                "name": "05_filtre_livrare_facturare.png",
                "wait": ".o_list_view .o_data_row",
                "eval": steps(("click", ".o_searchview_dropdown_toggler"), ("style", SPACE_FILTERS)),
                "highlight": [
                    {
                        "ro_RO": ".o_search_bar_menu .o_menu_item:has-text('Livrare')",
                        "en_US": ".o_search_bar_menu .o_menu_item:has-text('Delivery')",
                    },
                    {
                        "ro_RO": ".o_search_bar_menu .o_menu_item:has-text('Facturare')",
                        "en_US": ".o_search_bar_menu .o_menu_item:has-text('Invoice')",
                    },
                ],
            },
            {
                "url": self._form_url(),
                "name": "02_cnp_completare_automata.png",
                "wait": ".o_form_view div[name='name'] input",
                "eval": steps(
                    ("click", "div[name='company_type'] input[data-value='person']"),
                    ("type", "name", "Maria Ionescu"),
                    ("tab", PERSONAL_TAB),
                    ("type", "cnp", NEW_CNP),
                    ("style", PAD_FIELDS),
                ),
                "eval_wait": 1500,
                "highlight": ["div[name='cnp']", "div[name='birthdate']", "div[name='gender']"],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")

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
                "click": "div[name='company_type'] input[data-value='person']",
            },
            {"type": "Maria Ionescu", "into": "name", "hold": 400},
            {
                "caption": {
                    "ro_RO": "Datele de identitate au fila lor",
                    "en_US": "Identity data has its own tab",
                },
                "click": {
                    "ro_RO": "a.nav-link:text-is('Date personale')",
                    "en_US": "a.nav-link:text-is('Personal Data')",
                },
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
                "click": {
                    "ro_RO": "a.nav-link:text-is('Date personale')",
                    "en_US": "a.nav-link:text-is('Personal Data')",
                },
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
        # banner.json e în engleză: slide-ul RO primește textele lui
        intro_ro = {
            "title": "Date personale pe contacte",
            "summary": "CNP validat, carte de identitate și date din CNP",
            "features": [
                "Validarea cifrei de control a CNP",
                "Data nașterii și sexul din CNP",
                "Fila Date personale",
            ],
        }
        self.capture_gif(self._gif_steps(), intro=intro_ro)
        self.capture_gif(self._gif_steps(), lang="en_US")
