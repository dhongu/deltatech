# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestInterCompanyVendorStock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # the company where the stock moves happen is the vendor of the selling company
        cls.vendor_company = cls.env.company
        cls.selling_company = cls.env["res.company"].create({"name": "Inter Company Selling Company"})
        cls.env.user.company_ids |= cls.selling_company
        cls.other_partner = cls.env["res.partner"].create({"name": "Inter Company Other Vendor"})
        cls.product = cls.env["product.product"].create(
            {"name": "Inter Company Product", "is_storable": True, "company_id": False}
        )
        supplierinfo = cls.env["product.supplierinfo"]
        common = {"product_tmpl_id": cls.product.product_tmpl_id.id, "company_id": cls.selling_company.id}
        cls.variant_line = supplierinfo.create(
            dict(common, partner_id=cls.vendor_company.partner_id.id, product_id=cls.product.id)
        )
        cls.template_line = supplierinfo.create(dict(common, partner_id=cls.vendor_company.partner_id.id))
        cls.other_line = supplierinfo.create(dict(common, partner_id=cls.other_partner.id, qty_available=55))
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.vendor_company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.stock_location, 10)

    def _move(self, product, qty):
        move = self.env["stock.move"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": qty,
            }
        )
        move._action_confirm()
        return move

    def test_reservation_updates_vendor_lines(self):
        move = self._move(self.product, 3)
        move._action_assign()
        self.assertEqual(self.product.free_qty, 7)
        self.assertEqual(self.variant_line.qty_available, 7)
        self.assertEqual(self.template_line.qty_available, 7)
        self.assertEqual(self.other_line.qty_available, 55)

    def test_validation_updates_vendor_lines(self):
        move = self._move(self.product, 3)
        move._action_assign()
        (self.variant_line | self.template_line).qty_available = 0
        move.quantity = 3
        move.picked = True
        move._action_done()
        self.assertEqual(move.state, "done")
        self.assertEqual(self.variant_line.qty_available, 7)
        self.assertEqual(self.template_line.qty_available, 7)
        self.assertEqual(self.other_line.qty_available, 55)

    def test_product_without_vendor_line(self):
        product = self.env["product.product"].create({"name": "Inter Company No Vendor", "is_storable": True})
        self.env["stock.quant"]._update_available_quantity(product, self.stock_location, 4)
        move = self._move(product, 1)
        move._action_assign()
        self.assertFalse(
            self.env["product.supplierinfo"].search([("product_tmpl_id", "=", product.product_tmpl_id.id)])
        )
        self.assertEqual(self.variant_line.qty_available, 0)
