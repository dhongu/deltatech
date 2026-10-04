# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPurchasePriceMultiCompany(TransactionCase):
    """PURCHASEPRICE-001: the sale price update uses the currency of the active company, not of the
    default company of the user."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_str("purchase.update_list_price", "True")
        cls.company_a = cls.env.user.company_id
        currency_a = cls.company_a.currency_id
        currency_b = (
            cls.env["res.currency"]
            .with_context(active_test=False)
            .search([("id", "!=", currency_a.id), ("name", "in", ["EUR", "USD", "RON"])], limit=1)
        )
        currency_b.active = True
        cls.company_b = cls.env["res.company"].create({"name": "Price company B", "currency_id": currency_b.id})
        cls.env.user.company_ids |= cls.company_b
        today = fields.Date.today()
        # in company B: 1 unit of B currency = 5 units of A currency
        cls.env["res.currency.rate"].create(
            [
                {"currency_id": currency_b.id, "rate": 1.0, "name": today, "company_id": cls.company_b.id},
                {"currency_id": currency_a.id, "rate": 5.0, "name": today, "company_id": cls.company_b.id},
            ]
        )
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=[cls.company_a.id, cls.company_b.id]))
        cls.partner = cls.env["res.partner"].create({"name": "Supplier B"})
        cls.product = cls.env["product.product"].create(
            {"name": "Shared product", "is_storable": True, "trade_markup": 100, "taxes_id": [(6, 0, [])]}
        )

    def test_supplier_price_in_company_b(self):
        self.assertEqual(self.env.company, self.company_a)
        self.assertEqual(self.product.currency_id, self.company_a.currency_id)
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.partner.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "company_id": self.company_b.id,
                "currency_id": self.company_b.currency_id.id,
                "price": 100.0,
            }
        )
        self.assertEqual(self.product.with_company(self.company_b).last_purchase_price, 100.0)
        # cost 100 in B currency + 100% markup = 200 in B currency = 1000 in the product (A) currency
        expected = self.company_b.currency_id._convert(
            200.0, self.product.currency_id, self.company_b, fields.Date.today()
        )
        self.assertAlmostEqual(expected, 1000.0, places=2)
        self.assertAlmostEqual(self.product.list_price, expected, places=2)

    def test_onchange_with_active_company_b(self):
        product = self.product.with_company(self.company_b)
        product.last_purchase_price = 100.0
        product.product_tmpl_id.onchange_last_purchase_price()
        self.assertAlmostEqual(self.product.list_price, 1000.0, places=2)
