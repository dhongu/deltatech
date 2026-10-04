# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools.binary import BinaryBytes


@tagged("post_install", "-at_install")
class TestSearchProduct(TransactionCase):
    """PURCHASEXLS-001: the supplier code is matched on the order vendor and company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "XLS company B"})
        cls.env.user.company_ids |= cls.company_b
        cls.vendor = cls.env["res.partner"].create({"name": "XLS vendor"})
        cls.vendor_contact = cls.env["res.partner"].create({"name": "XLS vendor contact", "parent_id": cls.vendor.id})
        cls.other_vendor = cls.env["res.partner"].create({"name": "XLS other vendor"})
        cls.product_other = cls._product("Other vendor product")
        cls.product_b = cls._product("Company B product")
        cls.product_vendor = cls._product("Vendor product")
        # rows created first are found first by an unscoped search
        cls._seller(cls.product_other, cls.other_vendor, cls.company_a)
        cls._seller(cls.product_b, cls.vendor, cls.company_b)
        cls._seller(cls.product_vendor, cls.vendor, cls.company_a)

    @classmethod
    def _product(cls, name):
        return cls.env["product.product"].create({"name": name, "is_storable": True})

    @classmethod
    def _seller(cls, product, partner, company, code="SKU-1"):
        return cls.env["product.supplierinfo"].create(
            {
                "partner_id": partner.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_code": code,
                "company_id": company.id,
                "price": 10,
            }
        )

    def _wizard(self, partner, company=None):
        company = company or self.company_a
        order = (
            self.env["purchase.order"]
            .with_company(company)
            .create({"partner_id": partner.id, "company_id": company.id})
        )
        return (
            self.env["import.purchase.line"]
            .with_company(company)
            .with_context(active_id=order.id, active_model="purchase.order")
            .create({"data_file": BinaryBytes(b"x")})
        )

    def test_code_of_order_vendor(self):
        self.assertEqual(self._wizard(self.vendor).search_product("SKU-1"), self.product_vendor)
        self.assertEqual(self._wizard(self.other_vendor).search_product("SKU-1"), self.product_other)

    def test_code_of_vendor_contact(self):
        """An order placed on a contact of the vendor uses the pricing rows of the company partner."""
        self.assertEqual(self._wizard(self.vendor_contact).search_product("SKU-1"), self.product_vendor)

    def test_code_of_order_company(self):
        self.assertEqual(self._wizard(self.vendor, self.company_b).search_product("SKU-1"), self.product_b)

    def test_code_of_other_vendor_only(self):
        """A code known only for another vendor is not found."""
        self._seller(self._product("Only other"), self.other_vendor, self.company_a, code="SKU-2")
        self.assertFalse(self._wizard(self.vendor).search_product("SKU-2"))

    def test_ambiguous_code(self):
        self._seller(self._product("Second vendor product"), self.vendor, self.company_a)
        with self.assertRaises(UserError):
            self._wizard(self.vendor).search_product("SKU-1")
