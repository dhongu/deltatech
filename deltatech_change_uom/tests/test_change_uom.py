# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestChangeUoM(TransactionCase):
    def setUp(self):
        super().setUp()
        self.uom_unit = self.env.ref("uom.product_uom_unit")
        self.uom_dozen = self.env.ref("uom.product_uom_dozen")
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.product = self.env["product.template"].create(
            {
                "name": "Test Product",
                "uom_id": self.uom_unit.id,
                "seller_ids": [(0, 0, {"partner_id": self.partner.id, "price": 10})],
            }
        )
        variant = self.product.product_variant_id
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": variant.id, "product_uom_qty": 1})],
            }
        )
        self.purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": variant.id, "product_qty": 1})],
            }
        )

    def test_wizard(self):
        wizard = Form(self.env["product.change.uom"].with_context(active_id=self.product.id))
        self.assertEqual(wizard.uom_id, self.uom_unit)
        wizard.uom_id = self.uom_dozen
        wizard = wizard.save()
        wizard.with_context(active_id=self.product.id).do_change()

        self.assertEqual(self.product.uom_id, self.uom_dozen)
        self.assertEqual(self.product.product_variant_id.uom_id, self.uom_dozen)
        self.assertEqual(self.product.seller_ids.product_uom_id, self.uom_dozen)
        self.assertEqual(self.sale_order.order_line.product_uom_id, self.uom_dozen)
        self.assertEqual(self.purchase_order.order_line.product_uom_id, self.uom_dozen)
