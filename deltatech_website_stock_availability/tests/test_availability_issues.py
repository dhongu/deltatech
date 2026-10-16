# © 2008-2026 Deltatech / Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.website_sale.tests.common import MockRequest


@tagged("post_install", "-at_install")
class TestVendorAvailability(TransactionCase):
    """#3502: vendor stock and lead time come from the supplier that applies to the variant."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].create({"name": "Test Website", "company_id": cls.env.company.id})
        cls.vendor_a = cls.env["res.partner"].create({"name": "Vendor A"})
        cls.vendor_b = cls.env["res.partner"].create({"name": "Vendor B"})
        attribute = cls.env["product.attribute"].create(
            {"name": "Size", "value_ids": [(0, 0, {"name": "S"}), (0, 0, {"name": "L"})]}
        )
        cls.template = cls.env["product.template"].create(
            {
                "name": "Variant product",
                "is_storable": True,
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": attribute.id, "value_ids": [(6, 0, attribute.value_ids.ids)]})
                ],
            }
        )
        cls.variant_1, cls.variant_2 = cls.template.product_variant_ids

    def _info(self, product):
        with MockRequest(self.env, website=self.website):
            tmpl = product.product_tmpl_id.with_context(website_sale_stock_get_quantity=True)
            return tmpl._get_combination_info(product_id=product.id)

    def _seller(self, **vals):
        values = {
            "partner_id": self.vendor_a.id,
            "product_tmpl_id": self.template.id,
            "qty_available": 0,
            "delay": 7,
        }
        values.update(vals)
        return self.env["product.supplierinfo"].create(values)

    def test_seller_of_other_variant_ignored(self):
        self._seller(sequence=1, product_id=self.variant_1.id, qty_available=100, delay=2)
        self._seller(sequence=2, partner_id=self.vendor_b.id, qty_available=0, delay=7)
        info = self._info(self.variant_2)
        self.assertEqual(info["availability_vendor"], 0)
        self.assertEqual(info["purchase_lead_time"], 7)
        info = self._info(self.variant_1)
        self.assertEqual(info["availability_vendor"], 100)
        self.assertEqual(info["purchase_lead_time"], 2)

    def test_seller_of_other_company_ignored(self):
        other_company = self.env["res.company"].create({"name": "Other company"})
        self._seller(sequence=1, company_id=other_company.id, qty_available=100, delay=2)
        self._seller(sequence=2, partner_id=self.vendor_b.id, company_id=False, qty_available=3, delay=7)
        info = self._info(self.variant_2)
        self.assertEqual(info["availability_vendor"], 3)
        self.assertEqual(info["purchase_lead_time"], 7)

    def test_expired_and_archived_sellers_ignored(self):
        self._seller(sequence=1, date_end="2020-12-31", qty_available=100, delay=2)
        archived = self.env["res.partner"].create({"name": "Archived vendor"})
        self._seller(sequence=2, partner_id=archived.id, qty_available=50, delay=1)
        archived.action_archive()
        self._seller(sequence=3, partner_id=self.vendor_b.id, qty_available=4, delay=7)
        info = self._info(self.variant_2)
        self.assertEqual(info["availability_vendor"], 4)
        self.assertEqual(info["purchase_lead_time"], 7)

    def test_current_offer_preferred_to_future_one(self):
        self._seller(sequence=1, date_start="2099-01-01", qty_available=100, delay=2)
        self._seller(sequence=2, partner_id=self.vendor_b.id, qty_available=4, delay=7)
        info = self._info(self.variant_2)
        self.assertEqual(info["availability_vendor"], 4)
        self.assertEqual(info["purchase_lead_time"], 7)


@tagged("post_install", "-at_install")
class TestCartDeliveryBadge(TransactionCase):
    """#3503: cart badges use the website warehouse and the unit of the cart line."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.other_warehouse = cls.env["stock.warehouse"].create({"name": "Other WH", "code": "OWH"})
        cls.website = cls.env["website"].create(
            {"name": "Test Website", "company_id": cls.env.company.id, "warehouse_id": cls.warehouse.id}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Badge product",
                "is_storable": True,
                "list_price": 10,
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Customer"})
        cls.order = cls.env["sale.order"].create(
            {"partner_id": cls.partner.id, "website_id": cls.website.id, "warehouse_id": cls.warehouse.id}
        )

    def _render(self, qty, uom):
        line = self.env["sale.order.line"].create(
            {"order_id": self.order.id, "product_id": self.product.id, "product_uom_qty": qty, "product_uom_id": uom.id}
        )
        return str(self.env["ir.qweb"]._render("website_sale.cart_line_description_following_lines", {"line": line}))

    def test_stock_in_other_warehouse_not_immediate(self):
        self.env["stock.quant"]._update_available_quantity(self.product, self.other_warehouse.lot_stock_id, 10)
        html = self._render(1, self.env.ref("uom.product_uom_unit"))
        self.assertNotIn("Immediate delivery", html)
        self.assertIn("Subsequent delivery", html)

    def test_line_unit_converted(self):
        self.env["stock.quant"]._update_available_quantity(self.product, self.warehouse.lot_stock_id, 6)
        dozen = self.env.ref("uom.product_uom_dozen")
        html = self._render(1, dozen)
        self.assertIn("Subsequent delivery", html)
        # six units shown as half a dozen, not as 6
        self.assertIn(">0.5<", html)

    def test_enough_stock_in_website_warehouse(self):
        self.env["stock.quant"]._update_available_quantity(self.product, self.warehouse.lot_stock_id, 24)
        html = self._render(2, self.env.ref("uom.product_uom_dozen"))
        self.assertIn("Immediate delivery", html)
        self.assertNotIn("Subsequent delivery", html)
