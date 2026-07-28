from odoo.exceptions import ValidationError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestSaleMultiple(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Quantity Rules Partner"})
        cls.order = cls.env["sale.order"].create({"partner_id": cls.partner.id})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Quantity Rules Product",
                "list_price": 100.0,
                "qty_multiple": 5.0,
                "qty_minim": 10.0,
            }
        )

    def _create_line(self, product=None, quantity=1.0, product_uom=None):
        product = product or self.product
        return self.env["sale.order.line"].create(
            {
                "order_id": self.order.id,
                "product_id": product.id,
                "product_uom_id": (product_uom or product.uom_id).id,
                "product_uom_qty": quantity,
            }
        )

    def test_form_onchange_applies_minimum_and_multiple(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 7.0
            self.assertEqual(line_form.product_uom_qty, 10.0)

    def test_create_applies_quantity_rules(self):
        line = self._create_line(quantity=7.0)
        self.assertEqual(line.product_uom_qty, 10.0)

    def test_create_accepts_string_quantity(self):
        """EDI imports and data loads pass the quantity as a string: the rules
        must still apply instead of raising a TypeError on the comparison."""
        line = self._create_line(quantity="7.0")
        self.assertEqual(line.product_uom_qty, 10.0)

    def test_write_accepts_string_quantity(self):
        line = self._create_line(quantity=10.0)
        line.write({"product_uom_qty": "7.0"})
        self.assertEqual(line.product_uom_qty, 10.0)

    def test_batch_write_applies_rules_to_every_line(self):
        lines = self._create_line(quantity=10.0) | self._create_line(quantity=15.0)
        lines.write({"product_uom_qty": 7.0})
        self.assertRecordValues(lines, [{"product_uom_qty": 10.0}] * 2)

    def test_minimum_is_rounded_to_next_multiple(self):
        self.product.write({"qty_multiple": 10.0, "qty_minim": 15.0})
        line = self._create_line(quantity=1.0)
        self.assertEqual(line.product_uom_qty, 20.0)

    def test_rules_are_converted_to_line_uom(self):
        pack_of_six = self.env.ref("uom.product_uom_pack_6")
        self.product.write({"qty_multiple": 6.0, "qty_minim": 12.0})
        line = self._create_line(quantity=1.0, product_uom=pack_of_six)
        self.assertEqual(line.product_uom_qty, 2.0)

    def test_changing_uom_reapplies_rules(self):
        pack_of_six = self.env.ref("uom.product_uom_pack_6")
        self.product.write({"qty_multiple": 6.0, "qty_minim": 12.0})
        line = self._create_line(quantity=12.0)
        line.write({"product_uom_id": pack_of_six.id})
        self.assertEqual(line.product_uom_qty, 2.0)

    def test_template_minimum_tracks_variant(self):
        self.product.qty_minim = 17.0
        self.assertEqual(self.product.product_tmpl_id.qty_minim, 17.0)

    def test_negative_rules_are_rejected(self):
        with self.assertRaises(ValidationError):
            self.product.qty_multiple = -1.0
        with self.assertRaises(ValidationError):
            self.product.qty_minim = -1.0

    def test_new_product_has_no_minimum_by_default(self):
        product = self.env["product.product"].create({"name": "Fractional Product"})
        self.assertEqual(product.qty_minim, 0.0)
        line = self._create_line(product=product, quantity=0.25)
        self.assertEqual(line.product_uom_qty, 0.25)
