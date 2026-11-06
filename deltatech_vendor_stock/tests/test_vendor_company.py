# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestVendorStockCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Vendor Stock Company B"})
        cls.company_child = cls.env["res.company"].create(
            {"name": "Vendor Stock Child of A", "parent_id": cls.company_a.id}
        )
        cls.env.user.company_ids |= cls.company_b | cls.company_child
        cls.partner = cls.env["res.partner"].create({"name": "Vendor Stock Supplier"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Vendor Stock Shared Product",
                "is_storable": True,
                "company_id": False,
                "seller_ids": [
                    (0, 0, {"partner_id": cls.partner.id, "qty_available": 10, "company_id": cls.company_a.id}),
                    (0, 0, {"partner_id": cls.partner.id, "qty_available": 70, "company_id": cls.company_b.id}),
                    (0, 0, {"partner_id": cls.partner.id, "qty_available": 5, "company_id": False}),
                ],
            }
        )
        cls.all_companies = cls.company_a | cls.company_b | cls.company_child

    def _product(self, company):
        return self.product.with_context(allowed_company_ids=(company | self.all_companies).ids)

    def test_product_counts_only_current_company(self):
        self.assertEqual(self._product(self.company_a).vendor_qty_available, 15)
        self.assertEqual(self._product(self.company_b).vendor_qty_available, 75)

    def test_child_company_counts_parent_rows(self):
        self.assertEqual(self._product(self.company_child).vendor_qty_available, 15)

    def test_sale_line_uses_order_company(self):
        env = self.env(context=dict(self.env.context, allowed_company_ids=self.all_companies.ids))
        order = env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company_b.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 1})],
            }
        )
        self.assertEqual(env.company, self.company_a)
        self.assertEqual(order.order_line.vendor_qty_available, 75)
