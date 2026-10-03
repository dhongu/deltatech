# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCreateRuleMultiCompany(TransactionCase):
    """REORDER-001: the rules are generated for the active company, not for the default company of the user."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.user.company_id
        cls.company_b = cls.env["res.company"].create({"name": "Reorder company B"})
        cls.env.user.company_ids |= cls.company_b
        cls.warehouse_a = cls.env["stock.warehouse"].search([("company_id", "=", cls.company_a.id)], limit=1)
        cls.warehouse_b = cls.env["stock.warehouse"].search([("company_id", "=", cls.company_b.id)], limit=1)
        # the user keeps A as default company and works in B
        cls.env_b = cls.env(context=dict(cls.env.context, allowed_company_ids=[cls.company_b.id, cls.company_a.id]))

    def _rules(self, product):
        return (
            self.env["stock.warehouse.orderpoint"]
            .sudo()
            .with_context(active_test=False)
            .search([("product_id", "=", product.id)])
        )

    def test_create_product_in_active_company(self):
        self.assertTrue(self.warehouse_a.generate_reorder_rules)
        self.assertTrue(self.warehouse_b.generate_reorder_rules)
        self.assertEqual(self.env_b.company, self.company_b)
        self.assertEqual(self.env_b.user.company_id, self.company_a)
        product = self.env_b["product.product"].create({"name": "Shared product", "type": "consu", "is_storable": True})
        rules = self._rules(product)
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules.company_id, self.company_b)
        self.assertEqual(rules.location_id, self.warehouse_b.lot_stock_id)

    def test_product_of_company_b(self):
        """A product restricted to company B gets rules in B even if the active company is A."""
        product = self.env["product.product"].create(
            {"name": "Product B", "type": "consu", "is_storable": True, "company_id": self.company_b.id}
        )
        rules = self._rules(product)
        self.assertEqual(rules.company_id, self.company_b)
        self.assertEqual(rules.location_id, self.warehouse_b.lot_stock_id)

    def test_existing_rule_in_other_company(self):
        """A rule of the default company does not prevent the generation in the active company."""
        product = self.env["product.product"].create({"name": "Shared product", "type": "consu", "is_storable": True})
        self.assertEqual(self._rules(product).company_id, self.company_a)
        product.with_env(self.env_b).create_rule()
        rules = self._rules(product)
        self.assertEqual(rules.company_id, self.company_a | self.company_b)
