from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWeightUom(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Weight UoM Product",
                "uom_id": cls.uom_unit.id,
                "weight": 2.0,
                "l10n_ro_net_weight": 1.5,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Weight UoM Partner"})

    def _create_invoice(self, quantity, uom):
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_id": uom.id,
                            "quantity": quantity,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

    def test_invoice_weight_line_uom_converted(self):
        invoice = self._create_invoice(1, self.uom_dozen)
        self.assertAlmostEqual(invoice.weight, 24.0)
        self.assertAlmostEqual(invoice.weight_net, 18.0)

    def test_sale_order_weight_line_uom_converted(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_id": self.uom_dozen.id,
                            "product_uom_qty": 1,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )
        self.assertAlmostEqual(order.weight_gross, 24.0)
        self.assertAlmostEqual(order.weight_net, 18.0)

    def test_purchase_order_weight_line_uom_converted(self):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_id": self.uom_dozen.id,
                            "product_qty": 1,
                            "price_unit": 100,
                            "date_planned": fields.Datetime.now(),
                        },
                    )
                ],
            }
        )
        self.assertAlmostEqual(order.weight_gross, 24.0)
        self.assertAlmostEqual(order.weight_net, 18.0)

    def test_gross_weight_converted_from_pounds_to_kg(self):
        self.env["ir.config_parameter"].sudo().set_param("product.weight_in_lbs", "1")
        self.product.weight = 10.0  # 10 lb
        invoice = self._create_invoice(1, self.uom_unit)
        # 10 lb = 4.5359 kg, stored with the "Stock Weight" precision
        self.assertAlmostEqual(invoice.weight, 4.54, places=2)
