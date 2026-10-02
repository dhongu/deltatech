# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details

from lxml import etree

from odoo.tests import TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval


@tagged("post_install", "-at_install")
class TestSaleOrderSearch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({"name": "Test product search", "list_price": 10.0})
        cls.partner_a = cls.env["res.partner"].create(
            {"name": "Partner A", "email": "alpha.search@example.com", "phone": "+40 711 111 111"}
        )
        cls.partner_b = cls.env["res.partner"].create(
            {"name": "Partner B", "email": "beta.search@example.com", "phone": "+40 722 222 222"}
        )
        cls.order_a = cls.env["sale.order"].create(
            {"partner_id": cls.partner_a.id, "order_line": [(0, 0, {"product_id": cls.product.id})]}
        )
        cls.order_b = cls.env["sale.order"].create(
            {"partner_id": cls.partner_b.id, "order_line": [(0, 0, {"product_id": cls.product.id})]}
        )

    def _search_domain(self, label, value):
        view = self.env.ref("sale.view_sales_order_filter")
        arch = self.env["sale.order"].get_view(view.id, "search")["arch"]
        nodes = etree.fromstring(arch).xpath(f"//field[@name='partner_id'][@string='{label}']")
        self.assertEqual(len(nodes), 1, f"Search field {label} missing from sale order search view")
        return safe_eval(nodes[0].get("filter_domain"), {"self": value})

    def _search(self, label, value):
        domain = self._search_domain(label, value)
        orders = self.env["sale.order"].search(domain)
        return orders & (self.order_a | self.order_b)

    def test_search_by_email(self):
        self.assertEqual(self._search("E-mail", "alpha.search@"), self.order_a)
        self.assertEqual(self._search("E-mail", "beta.search"), self.order_b)
        self.assertEqual(self._search("E-mail", ".search@example.com"), self.order_a | self.order_b)

    def test_search_by_phone(self):
        self.assertEqual(self._search("Phone", "711 111"), self.order_a)
        self.assertEqual(self._search("Phone", "722"), self.order_b)
        self.assertFalse(self._search("Phone", "799 999"))
