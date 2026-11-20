# Copyright (C) 2026 Terrabit
# License OPL-1 (https://www.odoo.com/documentation/user/legal/licenses/licenses.html)
#
# Capturi de ecran pentru fișa consultant „Producție simplă" — RO pentru fișă, EN pentru USAGE.md.
#
# Seedează: o producție în Ciornă (ouă consumate în duzini, produsul obținut cu costul repartizat),
# una confirmată, una cu consumul parțial (4 din 10 disponibile, backorder „Întreabă") și una cu
# ofertă pentru produsul final.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i l10n_ro,deltatech_mrp_simple,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestMrpSimpleScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_mrp_simple"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Producție SRL")
        company = cls.env.company
        cls.env.ref("base.user_admin").write({"company_ids": [(4, company.id)], "company_id": company.id})
        env = cls.env

        stock = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        cls.stock_location = stock.lot_stock_id
        production = env["stock.location"].search(
            [("usage", "=", "production"), ("company_id", "=", company.id)], limit=1
        )

        def picking_type(name, code, src, dest, **vals):
            return env["stock.picking.type"].create(
                {
                    "name": name,
                    "code": "internal",
                    "sequence_code": code,
                    "default_location_src_id": src.id,
                    "default_location_dest_id": dest.id,
                    "warehouse_id": stock.id,
                    "company_id": company.id,
                    **vals,
                }
            )

        cls.type_consume = picking_type("Consum producție", "CPS", cls.stock_location, production)
        cls.type_consume_ask = picking_type(
            "Consum producție (întreabă)", "CPA", cls.stock_location, production, create_backorder="ask"
        )
        cls.type_receipt = picking_type("Recepție producție", "RPS", production, cls.stock_location)

        def product(name, cost, price, qty):
            rec = env["product.product"].create(
                {"name": name, "type": "consu", "is_storable": True, "standard_price": cost, "list_price": price}
            )
            if qty:
                env["stock.quant"]._update_available_quantity(rec, cls.stock_location, qty)
            return rec

        cls.eggs = product("Ouă", 1.2, 2.0, 200)
        cls.flour = product("Făină", 4.0, 6.0, 4)
        cls.cake = product("Tort aniversar", 0.0, 80.0, 0)
        cls.partner = env["res.partner"].create({"name": "Cofetăria Dulce SRL", "country_id": env.ref("base.ro").id})
        cls.dozen = env.ref("uom.product_uom_dozen")

        def simple(out, picking_type_consume, **vals):
            return env["mrp.simple"].create(
                {
                    "picking_type_consume": picking_type_consume.id,
                    "picking_type_receipt_production": cls.type_receipt.id,
                    "validation_consume": True,
                    "product_out_ids": [
                        (0, 0, {"product_id": p.id, "quantity": q, "uom_id": u.id, "price_unit": p.standard_price})
                        for p, q, u in out
                    ],
                    "product_in_ids": [
                        (0, 0, {"product_id": cls.cake.id, "quantity": 1, "uom_id": cls.cake.uom_id.id}),
                    ],
                    **vals,
                }
            )

        unit = env.ref("uom.product_uom_unit")
        cls.mrp_draft = simple([(cls.eggs, 2, cls.dozen)], cls.type_consume, name="PS/0001")
        cls.mrp_draft.compute_finit_price()
        cls.mrp_done = simple([(cls.eggs, 1, cls.dozen)], cls.type_consume, name="PS/0002")
        cls.mrp_done.compute_finit_price()
        cls.mrp_done.do_transfer()
        cls.mrp_partial = simple([(cls.flour, 10, unit)], cls.type_consume_ask, name="PS/0003")
        cls.mrp_partial.compute_finit_price()
        cls.mrp_sale = simple(
            [(cls.eggs, 1, cls.dozen)],
            cls.type_consume,
            name="PS/0004",
            auto_create_sale=True,
            partner_id=cls.partner.id,
            final_product_name="Tort aniversar premium",
            final_product_category=env.ref("product.product_category_goods").id,
            final_product_uom_id=unit.id,
        )
        cls.mrp_sale.compute_finit_price()
        cls.mrp_sale.sudo().do_transfer()

    def _form(self, rec):
        return f"id={rec.id}&model=mrp.simple&view_type=form"

    def _shots(self):
        return [
            {
                "url": self._form(self.mrp_draft),
                "name": "01_document_nou.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='picking_type_consume']", "div[name='picking_type_receipt_production']"],
                "settle": 2000,
            },
            {
                "url": self._form(self.mrp_draft),
                "name": "02_linii_consum.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='product_out_ids']"],
                "settle": 2000,
            },
            {
                "url": self._form(self.mrp_draft),
                "name": "03_linii_receptie.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='product_in_ids']", "button[name='compute_finit_price']"],
                "settle": 2000,
            },
            {
                "url": self._form(self.mrp_done),
                "name": "04_confirmat.png",
                "wait": ".o_form_view",
                "highlight": ["button[name='open_consume']", "button[name='open_receipt']"],
                "settle": 2000,
            },
            {
                "url": self._form(self.mrp_partial),
                "name": "05_dialog_backorder.png",
                "wait": ".o_form_view",
                "click_btn": "button[name='do_transfer']",
                "wait_after": ".modal",
                "settle": 3500,
            },
            {
                "url": f"id={self.mrp_sale.sale_order_id.id}&model=sale.order&view_type=form",
                "name": "06_oferta_mrp_simple.png",
                "wait": ".o_form_view",
                "highlight": ["button[name='action_view_mrp']"],
                "settle": 2000,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
