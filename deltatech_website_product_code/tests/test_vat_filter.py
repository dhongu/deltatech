# ©  2015-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import HttpCase, new_test_user


@tagged("post_install", "-at_install")
class TestVatFilter(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.supplier = cls.env["res.partner"].create({"name": "Supplier VAT Test", "vat": "RO99999999"})
        cls.product = cls.env["product.template"].create(
            {
                "name": "Vat Oracle Product",
                "default_code": "VATORACLE001",
                "type": "consu",
                "is_published": True,
                "sale_ok": True,
                "seller_ids": [(0, 0, {"partner_id": cls.supplier.id, "price": 1})],
            }
        )
        new_test_user(cls.env, login="vat_internal", password="vat_internal", groups="base.group_user")

    def _search(self, vat=None):
        url = "/shop/products-search?search=VATORACLE001"
        if vat:
            url += f"&vat={vat}"
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        return response.text

    def test_public_vat_ignored(self):
        """Un anonim primește același rezultat cu și fără vat."""
        without_vat = self._search()
        self.assertIn("VATORACLE001", without_vat)
        self.assertEqual(self._search(vat="RO99999999"), without_vat)

    def test_internal_vat_applied(self):
        """Pentru un utilizator intern, vat exclude produsele furnizorului."""
        self.authenticate("vat_internal", "vat_internal")
        self.assertIn("VATORACLE001", self._search())
        self.assertNotIn("VATORACLE001", self._search(vat="RO99999999"))
