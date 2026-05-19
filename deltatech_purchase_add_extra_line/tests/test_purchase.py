# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestPurchaseAddExtraLine(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create a vendor
        self.vendor = self.env["res.partner"].create({"name": "Vendor A", "supplier_rank": 1})

        seller_ids = [(0, 0, {"partner_id": self.vendor.id})]

        # Extra product (will be auto-added)
        self.extra_product = self.env["product.product"].create(
            {
                "name": "Extra Product",
                "type": "consu",
                "standard_price": 20.0,
                "list_price": 30.0,
                "seller_ids": seller_ids,
            }
        )
        # Main product configured to add the extra product
        self.main_product = self.env["product.product"].create(
            {
                "name": "Main Product",
                "type": "consu",
                "standard_price": 100.0,
                "list_price": 150.0,
                "seller_ids": seller_ids,
                "extra_product_id": self.extra_product.id,
                "extra_percent": 10.0,  # price of extra line = 10% of main line price
                "extra_qty": 2.0,  # qty of extra line = 2x main qty
            }
        )

    def test_purchase_extra_line_creation_update_and_unlink(self):
        # Create RFQ
        po_form = Form(self.env["purchase.order"])
        po_form.partner_id = self.vendor
        with po_form.order_line.new() as line_form:
            line_form.product_id = self.main_product
            line_form.product_qty = 5
        po = po_form.save()

        # After saving, an extra line should be present
        self.assertEqual(len(po.order_line), 2, "There should be two lines: main and extra")

        # Identify lines
        main_line = po.order_line.filtered(lambda l: l.product_id == self.main_product)
        self.assertEqual(len(main_line), 1, "Exactly one main line expected")
        extra_line = po.order_line.filtered(lambda l: l.product_id == self.extra_product)
        self.assertEqual(len(extra_line), 1, "Exactly one extra line expected")

        # Both lines should share the same line_uuid
        self.assertTrue(main_line.line_uuid, "Main line must have a line_uuid set")
        self.assertEqual(
            main_line.line_uuid,
            extra_line.line_uuid,
            "Main and extra lines should share the same line_uuid",
        )

        # Quantities and price unit checks
        self.assertEqual(
            extra_line.product_qty,
            5 * 2.0,
            "Extra line quantity should be main_qty * extra_qty",
        )
        # price_unit of extra line = main price * extra_percent / 100
        self.assertAlmostEqual(
            extra_line.price_unit,
            main_line.price_unit * 0.10,
            msg="Extra line price should be 10% of main line price",
        )

        # Update main quantity and re-check propagation
        main_line.product_qty = 7
        # In a real form, onchange would handle this; call method explicitly for the test
        main_line.check_extra_product()
        self.assertEqual(
            extra_line.product_qty,
            7 * 2.0,
            "After update, extra line quantity should follow main qty",
        )

        # Deleting main line should remove the paired extra line too
        main_line.unlink()
        self.assertEqual(len(po.order_line), 0, "Both main and extra lines should be removed after unlink")
