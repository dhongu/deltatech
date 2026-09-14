# © 2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Buton Creează factură" — generate în timpul testelor, în RO.
#
# Seedează: o comandă de achiziție confirmată cu „Referință furnizor" completată (pentru pasul
# butonului evidențiat) și o factură deja creată din ea (pentru pasul de verificare a referinței
# copiate pe factură).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_purchase_create_bill_button,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPurchaseCreateBillButtonScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_purchase_create_bill_button"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Achiziții SRL")
        company = cls.env.company
        cls.env.ref("base.user_admin").write({"company_ids": [(4, company.id)], "company_id": company.id})

        env = cls.env
        cls.vendor = env["res.partner"].create({"name": "Furnizor Demo SRL", "country_id": env.ref("base.ro").id})
        cls.product = env["product.product"].create(
            {"name": "Materiale birou", "type": "consu", "purchase_method": "purchase"}
        )

        def make_order(partner_ref):
            order = env["purchase.order"].create(
                {
                    "partner_id": cls.vendor.id,
                    "partner_ref": partner_ref,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": cls.product.id,
                                "product_qty": 10.0,
                                "price_unit": 150.0,
                            },
                        )
                    ],
                }
            )
            order.button_confirm()
            return order

        # 1. comanda confirmată, cu Referință furnizor completată — rămâne nefacturată,
        #    pentru ca butonul „Creează factură" să fie vizibil în pașii 1 și 2
        cls.purchase_order = make_order("FV-2026-0042")

        # 2. a doua comandă, facturată imediat, pentru pasul 3 (factura cu Referința preluată)
        source_order = make_order("FV-2026-0051")
        cls.invoice = env["account.move"].browse(source_order.action_create_invoice()["res_id"])
        cls.invoice.invoice_date = fields.Date.today()

    def test_capture_fise(self):
        self.capture_screenshots(
            [
                # 1. Comanda de achiziție confirmată, cu Referință furnizor completată
                {
                    "url": f"id={self.purchase_order.id}&model=purchase.order&view_type=form",
                    "name": "01_comanda_confirmata.png",
                    "wait": ".o_form_view",
                    "highlight": [".o_field_widget[name='partner_ref']"],
                    "settle": 2000,
                    "full": True,
                },
                # 2. Butonul „Creează factură" evidențiat, lângă widget-ul de încărcare
                {
                    "url": f"id={self.purchase_order.id}&model=purchase.order&view_type=form",
                    "name": "02_buton_creare_factura.png",
                    "wait": ".o_form_view",
                    "highlight": ["button[name='action_create_invoice']"],
                    "settle": 2000,
                    "full": True,
                },
                # 3. Factura generată, cu Referință și Referință plată preluate din comandă
                {
                    "url": f"id={self.invoice.id}&model=account.move&view_type=form",
                    "name": "03_factura_generata.png",
                    "wait": ".o_form_view",
                    "highlight": [".o_field_widget[name='ref']", ".o_field_widget[name='payment_reference']"],
                    "settle": 2500,
                    "full": True,
                },
            ],
            viewport=(1500, 1000),
        )
