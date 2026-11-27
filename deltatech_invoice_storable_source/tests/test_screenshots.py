# © 2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Facturarea produselor stocabile doar din comenzi" — generate în
# timpul testelor, în limba RO, pe o companie românească în RON.
#
# Rulare — RESTRÂNSĂ LA CLASĂ, altfel se rescriu capturile tuturor modulelor cu test de fișe:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_invoice_storable_source,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=/deltatech_invoice_storable_source:TestInvoiceStorableSourceScreenshots \
#       --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

MODAL = ".modal-dialog .modal-body"
SALE_SETTING = "#check_storable_sale_source"
PURCHASE_SETTING = "#check_storable_purchase_source"


@tagged("-at_install", "post_install", "fise_screenshots")
class TestInvoiceStorableSourceScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_invoice_storable_source"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        env = cls.env
        cls.company = cls.prepare_ro_company(name="Depozit Demo SRL")
        env.ref("base.user_admin").write({"company_ids": [Command.link(cls.company.id)], "company_id": cls.company.id})
        cls.company.write({"check_storable_sale_source": True, "check_storable_purchase_source": True})

        cls.customer = env["res.partner"].create({"name": "Client Demo SRL"})
        cls.vendor = env["res.partner"].create({"name": "Furnizor Demo SRL"})
        cls.product = env["product.product"].create(
            {"name": "Marfă depozit", "is_storable": True, "list_price": 100.0, "standard_price": 60.0}
        )
        cls.out_invoice = cls._draft_invoice("out_invoice", cls.customer)
        cls.in_invoice = cls._draft_invoice("in_invoice", cls.vendor)

    @classmethod
    def _draft_invoice(cls, move_type, partner):
        return cls.env["account.move"].create(
            {
                "move_type": move_type,
                "company_id": cls.company.id,
                "partner_id": partner.id,
                "invoice_date": "2026-11-16",
                "invoice_line_ids": [(0, 0, {"product_id": cls.product.id, "quantity": 1.0, "price_unit": 100.0})],
            }
        )

    def _setting_shot(self, name, setting, block="center"):
        return {
            "url": f"action={self.env.ref('account.action_account_config').id}",
            "name": name,
            "wait": setting,
            "timeout": 60000,
            "eval": f"document.querySelector('{setting}').scrollIntoView({{block: '{block}'}})",
            "highlight": setting,
            "settle": 2000,
        }

    def _shots(self):
        return [
            self._setting_shot("01_setare_facturi_clienti.png", SALE_SETTING, block="end"),
            self._setting_shot("02_setare_facturi_furnizori.png", PURCHASE_SETTING),
            {
                "path": f"/odoo/action-account.action_move_out_invoice_type/{self.out_invoice.id}",
                "name": "03_factura_client_fara_comanda.png",
                "click_btn": "button[name='action_post']",
                "wait_after": MODAL,
            },
            {
                "path": f"/odoo/action-account.action_move_in_invoice_type/{self.in_invoice.id}",
                "name": "04_factura_furnizor_fara_comanda.png",
                "click_btn": "button[name='action_post']",
                "wait_after": MODAL,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
