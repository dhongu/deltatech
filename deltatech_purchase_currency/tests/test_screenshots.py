# © 2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Comandă de achiziție în valută, factură în moneda jurnalului” —
# generate în timpul testelor, pe compania „Demo Achiziții SRL” în RON: în RO pentru fișă și în EN
# (static/description/en/) pentru readme/USAGE.md, plus GIF-ul demo pentru Apps Store.
#
# Seedează cursul EUR (ieri și cu o lună în urmă), jurnalul de achiziții fără monedă,
# două jurnale de facturi furnizor în EUR, furnizorul român „Aluprof Distribuție SRL” și câte o comandă
# în EUR pentru fiecare criteriu de acceptare din readme/BRIEF.md (CA1–CA11), cu factura ei.
#
# Rulare:
#   .venv/bin/python odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_purchase_currency,l10n_ro,deltatech_doc_screenshots \
#       --test-tags=/deltatech_purchase_currency:TestPurchaseCurrencyScreenshots --stop-after-init
import unittest

from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.tests import Form, tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

RATE_TODAY = 5.0912
RATE_EARLIER = 5.0785
VENDOR_RATE = 5.10

# Afișează coloanele opționale cerute din lista de linii a facturii.
SHOW_COLUMNS = """
    new Promise((resolve) => {
        const wait = (ms) => new Promise((r) => setTimeout(r, ms));
        (async () => {
            try {
                await wait(800);
                const toggle = () => document.querySelector(
                    ".o_field_widget[name='invoice_line_ids'] .o_optional_columns_dropdown_toggle"
                );
                if (!toggle()) {
                    return;
                }
                toggle().click();
                await wait(800);
                for (const name of %s) {
                    const input = document.querySelector(`.o_optional_columns_dropdown input[name='${name}']`);
                    if (input && !input.checked) {
                        input.click();
                        await wait(500);
                    }
                }
                if (toggle()) {
                    toggle().click();
                }
                await wait(800);
            } finally {
                resolve();
            }
        })();
    })
"""

# Bifează în listă comanda dată, ca să apară butonul „Create Bills” din antet.
SELECT_ORDER = """
    new Promise((resolve) => {
        const wait = (ms) => new Promise((r) => setTimeout(r, ms));
        (async () => {
            try {
                for (let i = 0; i < 50; i++) {
                    const row = [...document.querySelectorAll(".o_list_view tr.o_data_row")].find(
                        (r) => r.querySelector("td[name='name']")?.textContent.trim() === "%s"
                    );
                    const input = row && row.querySelector("td.o_list_record_selector input");
                    if (input && !input.checked) {
                        input.click();
                    }
                    if (document.querySelector("button[name='action_create_invoice']")) {
                        break;
                    }
                    await wait(200);
                }
                await wait(800);
            } finally {
                resolve();
            }
        })();
    })
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPurchaseCurrencyScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_purchase_currency"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Achiziții SRL")
        company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        for xmlid in ("uom.group_uom", "purchase.group_purchase_manager", "base.group_multi_currency"):
            group = env.ref(xmlid)
            env.user.group_ids = [Command.link(group.id)]
            admin.group_ids = [Command.link(group.id)]
        # cumpărătorul de pe comenzi e utilizatorul testului; numele lui implicit apare în capturi
        env.user.name = "Andrei Popescu"
        env["res.config.settings"].create({"group_uom": True}).execute()
        env.flush_all()

        cls.today = fields.Date.context_today(admin)
        cls.bill_date = cls.today - relativedelta(days=18)
        cls.eur = env.ref("base.EUR")
        cls.eur.active = True
        env["res.currency.rate"].search([("currency_id", "=", cls.eur.id)]).unlink()
        # Odoo 20 folosește cursul cu data strict anterioară datei documentului (cursul BNR
        # publicat ieri e cursul de azi)
        env["res.currency.rate"].create(
            [
                {
                    "name": cls.today - relativedelta(months=1),
                    "currency_id": cls.eur.id,
                    "company_id": company.id,
                    "inverse_company_rate": RATE_EARLIER,
                },
                {
                    "name": cls.today - relativedelta(days=1),
                    "currency_id": cls.eur.id,
                    "company_id": company.id,
                    "inverse_company_rate": RATE_TODAY,
                },
            ]
        )

        cls.journal_ron = env["account.journal"].search(
            [("company_id", "=", company.id), ("type", "=", "purchase")], order="sequence, id", limit=1
        )
        cls.journal_ron.currency_id = False
        # două jurnale în EUR: pe primul îl alege Odoo singur pentru o factură în EUR (CA3), pe
        # al doilea îl pune comanda (CA4), ca să se vadă că factura ia jurnalul din comandă
        cls.journal_eur_default, cls.journal_eur = env["account.journal"].create(
            [
                {
                    "name": "Facturi furnizor EUR",
                    "code": "FEUR",
                    "type": "purchase",
                    "sequence": 20,
                    "currency_id": cls.eur.id,
                    "company_id": company.id,
                },
                {
                    "name": "Facturi import EUR",
                    "code": "FIMP",
                    "type": "purchase",
                    "sequence": 30,
                    "currency_id": cls.eur.id,
                    "company_id": company.id,
                },
            ]
        )

        ro = env.ref("base.ro").id
        cls.vendor = env["res.partner"].create({"name": "Aluprof Distribuție SRL", "country_id": ro})
        cls.profile = env["product.product"].create(
            {"name": "Profil aluminiu 40x40", "type": "consu", "purchase_method": "purchase"}
        )
        cls.corner = env["product.product"].create(
            {"name": "Colțar aluminiu 40", "type": "consu", "purchase_method": "purchase"}
        )
        cls.uom_unit = env.ref("uom.product_uom_unit")
        cls.uom_dozen = env.ref("uom.product_uom_dozen")

        # comanda din pașii 1-2 (încă nefacturată: butonul „Create Bills” din listă)
        cls.po_main = cls._create_po(cls.journal_ron)
        # CA1: factură în lei, la cursul de azi
        cls.bill_ca1 = cls._create_bill(cls._create_po(cls.journal_ron))
        # CA2: aceeași situație, cu data facturii de acum 18 zile
        cls.bill_ca2 = cls._create_bill(cls._create_po(cls.journal_ron))
        with Form(cls.bill_ca2) as form:
            form.invoice_date = cls.bill_date
        # CA3: fără jurnal de facturare, factura rămâne în EUR
        cls.bill_ca3 = cls._create_bill(cls._create_po())
        # CA4: jurnal în EUR
        cls.bill_ca4 = cls._create_bill(cls._create_po(cls.journal_eur))
        # CA5: linia facturii în duzine, apoi data facturii
        cls.bill_ca5 = cls._create_bill(cls._create_po(cls.journal_ron, price=10.0, qty=24.0))
        with Form(cls.bill_ca5) as form:
            with form.invoice_line_ids.edit(0) as line:
                line.product_uom_id = cls.uom_dozen
                line.quantity = 2.0
            form.invoice_date = cls.bill_date
        # CA6: două linii, a doua cu prețul schimbat de mână
        cls.bill_ca6 = cls._create_bill(cls._create_po(cls.journal_ron, corner=True))
        with Form(cls.bill_ca6) as form:
            with form.invoice_line_ids.edit(1) as line:
                line.price_unit = 6.50
        # CA7: factură nouă completată automat din comandă
        cls.po_ca7 = cls._create_po(cls.journal_ron, qty=80.0)
        form = Form(env["account.move"].with_context(default_move_type="in_invoice"))
        form.partner_id = cls.vendor
        form.invoice_date = cls.bill_date
        with mute_logger("odoo.tests.form.onchange"):
            form.purchase_vendor_bill_id = env["purchase.bill.union"].browse(-cls.po_ca7.id)
        cls.bill_ca7 = form.save()
        # CA8-CA11: cursul scris de furnizor pe factură; data facturii completată după curs nu
        # mai schimbă prețul (12,50 EUR × 5,10 = 63,75 lei), iar coloana de potrivire nu
        # semnalează linia
        cls.bill_ca9 = cls._create_bill(cls._create_po(cls.journal_ron))
        with Form(cls.bill_ca9) as form:
            form.purchase_vendor_rate = VENDOR_RATE
            form.invoice_date = cls.bill_date

    @classmethod
    def _create_po(cls, journal=None, price=12.50, qty=100.0, corner=False):
        lines = [
            Command.create(
                {"product_id": cls.profile.id, "product_qty": qty, "uom_id": cls.uom_unit.id, "price_unit": price}
            )
        ]
        if corner:
            lines.append(
                Command.create(
                    {"product_id": cls.corner.id, "product_qty": 200.0, "uom_id": cls.uom_unit.id, "price_unit": 1.20}
                )
            )
        # numere fixe: secvența comenzilor nu revine la rollback, iar fișa le citează
        cls.po_number = getattr(cls, "po_number", 9) + 1
        po = cls.env["purchase.order"].create(
            {
                "name": f"P{cls.po_number:05d}",
                "partner_id": cls.vendor.id,
                "currency_id": cls.eur.id,
                "journal_id": journal.id if journal else False,
                "order_line": lines,
            }
        )
        po.button_confirm()
        return po

    @classmethod
    def _create_bill(cls, po):
        po.action_create_invoice()
        return po.invoice_ids

    def _url(self, record):
        if record._name == "purchase.order":
            action = self.env.ref("purchase.purchase_form_action")
            menu = self.env.ref("purchase.menu_purchase_form_action")
        else:
            action = self.env.ref("account.action_move_in_invoice")
            menu = self.env.ref("account.menu_action_move_in_invoice_type")
        return f"action={action.id}&menu_id={menu.id}&id={record.id}&model={record._name}&view_type=form"

    def _bill_shot(self, bill, name, highlight, columns=None):
        shot = {
            "url": self._url(bill),
            "name": name,
            "wait": ".o_form_view",
            "highlight": highlight,
            "settle": 2000,
        }
        if columns:
            shot["eval"] = SHOW_COLUMNS % columns
        return shot

    def _shots(self):
        action = self.env.ref("purchase.purchase_form_action")
        menu = self.env.ref("purchase.menu_purchase_form_action")
        # moneda din rândul Jurnal (rândul Curs furnizor are și el un câmp currency_id)
        head = ["div[name='journal_id']", "div[name='journal_div'] div[name='currency_id']"]
        price = ".o_field_widget[name='invoice_line_ids'] td[name='price_unit']"
        return [
            # 1. comanda în EUR, jurnalul de facturare în tab-ul Other Info
            {
                "url": self._url(self.po_main),
                "name": "01_comanda_jurnal_facturare.png",
                "wait": ".o_form_view",
                "click_tab": "Other Info",
                "highlight": ["div[name='currency_id']", "div[name='journal_id']"],
                "settle": 2000,
            },
            # 2. lista comenzilor: comanda bifată și butonul de creare a facturilor
            {
                "url": f"action={action.id}&menu_id={menu.id}&model=purchase.order&view_type=list",
                "name": "02_creare_factura_din_lista.png",
                "wait": ".o_list_view",
                "eval": SELECT_ORDER % self.po_main.name,
                "highlight": ["button[name='action_create_invoice']"],
                "settle": 2000,
            },
            # 3. CA1: factura în lei, la cursul de azi
            self._bill_shot(self.bill_ca1, "03_factura_lei_curs_azi.png", [*head, price]),
            # 4. CA2: data facturii schimbată, preț la cursul acelei zile
            self._bill_shot(self.bill_ca2, "04_factura_data_reconversie.png", ["div[name='invoice_date']", price]),
            # 5. CA3: fără jurnal de facturare, factura rămâne în EUR
            self._bill_shot(self.bill_ca3, "05_factura_fara_jurnal_eur.png", [*head, price]),
            # 6. CA4: jurnal în EUR
            self._bill_shot(self.bill_ca4, "06_factura_jurnal_eur.png", [*head, price]),
            # 7. CA5: linia în duzine
            self._bill_shot(
                self.bill_ca5,
                "07_factura_unitate_duzina.png",
                [".o_field_widget[name='invoice_line_ids'] td[name='product_uom_id']", price],
                columns='["product_uom_id"]',
            ),
            # 8. CA6: indicatorul de potrivire a prețului
            self._bill_shot(
                self.bill_ca6,
                "08_indicator_potrivire_pret.png",
                [".o_field_widget[name='invoice_line_ids'] tr.o_data_row:nth-child(2) td[name='purchase_line_id']"],
                columns='["purchase_line_id"]',
            ),
            # 9. CA7: factură completată automat din comandă
            self._bill_shot(
                self.bill_ca7,
                "09_factura_completare_automata.png",
                [*head, ".o_field_widget[name='invoice_line_ids'] td[name='purchase_line_id']"],
                columns='["purchase_line_id"]',
            ),
            # 10. CA8-CA11: cursul furnizorului lângă data facturii, prețul la acest curs
            self._bill_shot(
                self.bill_ca9,
                "10_factura_curs_furnizor.png",
                ["div[name='purchase_vendor_rate_div']", "div[name='invoice_date']", price],
                columns='["purchase_line_id"]',
            ),
        ]

    def _gif_steps(self):
        po_url = self._url(self.po_main)
        bill1_url = self._url(self.bill_ca1)
        bill2_url = self._url(self.bill_ca2)
        tab = ".o_notebook .nav-link[name='purchase_delivery_invoice']"
        price = ".o_field_widget[name='invoice_line_ids'] td[name='price_unit']"
        return [
            {"goto": po_url, "wait": ".o_form_view"},
            {
                "caption": {"ro_RO": "Comanda e în EUR", "en_US": "The order is in EUR"},
                "move": "div[name='currency_id']",
                "hold": 2000,
            },
            {"click": tab, "hold": 800},
            {
                "caption": {
                    "ro_RO": "Jurnalul de facturare decide moneda facturii",
                    "en_US": "The invoicing journal decides the bill currency",
                },
                "move": "div[name='journal_id']",
                "hold": 2500,
            },
            {"goto": bill1_url, "wait": ".o_form_view"},
            {
                "caption": {
                    "ro_RO": "Factura vine în lei, la cursul de azi",
                    "en_US": "The bill comes in RON, at today's rate",
                },
                "move": price,
                "hold": 3000,
            },
            {"goto": bill2_url, "wait": ".o_form_view"},
            {
                "caption": {
                    "ro_RO": "Data facturii reconvertește prețul",
                    "en_US": "The bill date converts the price again",
                },
                "move": "div[name='invoice_date']",
                "hold": 2000,
            },
            {"move": price, "hold": 2500},
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), hide_systray=True, lang="en_US")

    def test_capture_gif(self):
        # suita deltatech are doar pagina EN pe Apps Store: GIF-ul RO nu se folosește
        self.capture_gif(self._gif_steps(), lang="en_US")
