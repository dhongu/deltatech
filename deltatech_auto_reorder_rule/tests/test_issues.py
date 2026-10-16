# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAutoReorderRuleIssues(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.warehouse_1 = cls.env["stock.warehouse"].search([("company_id", "=", cls.company_a.id)], limit=1)
        cls.warehouse_2 = cls.env["stock.warehouse"].create(
            {"name": "Reorder W2", "code": "RW2", "company_id": cls.company_a.id}
        )
        cls.orderpoint_model = cls.env["stock.warehouse.orderpoint"].with_context(active_test=False)

    def _rules(self, product):
        return self.orderpoint_model.search([("product_id", "=", product.id)])

    def test_rule_missing_in_one_warehouse(self):
        """#3364: an existing rule in W1 does not prevent the rule in W2, and no duplicate is created."""
        self.env["ir.config_parameter"].sudo().set_param("deltatech_auto_reorder_rule.dont_auto_create_rule", "True")
        product = self.env["product.product"].create({"name": "Reorder W1 W2", "type": "consu", "is_storable": True})
        self.assertFalse(self._rules(product))
        self.orderpoint_model.create(
            {
                "product_id": product.id,
                "location_id": self.warehouse_1.lot_stock_id.id,
                "product_min_qty": 3,
                "product_max_qty": 7,
            }
        )
        product.create_rule()
        rules = self._rules(product)
        self.assertEqual(rules.location_id, self.warehouse_1.lot_stock_id | self.warehouse_2.lot_stock_id)
        self.assertEqual(len(rules), 2)
        rule_w1 = rules.filtered(lambda r: r.location_id == self.warehouse_1.lot_stock_id)
        self.assertEqual(rule_w1.product_min_qty, 3)
        product.create_rule()
        self.assertEqual(len(self._rules(product)), 2)

    def test_dont_auto_create_rule_param(self):
        """#3365: only an enabled value of the parameter disables the automatic rules."""
        param = "deltatech_auto_reorder_rule.dont_auto_create_rule"
        for value, expected in [("False", True), ("0", True), ("", True), ("True", False), ("1", False)]:
            self.env["ir.config_parameter"].sudo().set_param(param, value)
            product = self.env["product.product"].create(
                {"name": f"Reorder param {value}", "type": "consu", "is_storable": True}
            )
            self.assertEqual(bool(self._rules(product)), expected, f"value {value!r}")

    def test_wizard_location_other_company(self):
        """#3366: the wizard creates the rule in the company of the location, with a route of that company."""
        company_b = self.env["res.company"].create({"name": "Reorder wizard company B"})
        self.env.user.company_ids |= company_b
        warehouse_b = self.env["stock.warehouse"].search([("company_id", "=", company_b.id)], limit=1)
        route_a = self.env["stock.route"].create(
            {"name": "Auto route A", "use_this_for_auto_rules": True, "company_id": self.company_a.id, "sequence": 1}
        )
        route_b = self.env["stock.route"].create(
            {"name": "Auto route B", "use_this_for_auto_rules": True, "company_id": company_b.id, "sequence": 2}
        )
        self.env["ir.config_parameter"].sudo().set_param("deltatech_auto_reorder_rule.dont_auto_create_rule", "True")
        product = self.env["product.product"].create({"name": "Reorder wizard", "type": "consu", "is_storable": True})
        env = self.env(context=dict(self.env.context, allowed_company_ids=[self.company_a.id, company_b.id]))
        locations = self.warehouse_1.lot_stock_id | warehouse_b.lot_stock_id
        wizard = (
            env["order.rules.details.wizard"]
            .with_context(active_id=product.product_tmpl_id.id)
            .create(
                {
                    "min_quantity": 1,
                    "max_quantity": 5,
                    "trigger": "manual",
                    "stock_location_ids": [(6, 0, locations.ids)],
                }
            )
        )
        wizard.do_create()
        rules = self._rules(product).sudo()
        self.assertEqual(len(rules), 2)
        rule_a = rules.filtered(lambda r: r.location_id == self.warehouse_1.lot_stock_id)
        rule_b = rules.filtered(lambda r: r.location_id == warehouse_b.lot_stock_id)
        self.assertEqual(rule_a.company_id, self.company_a)
        self.assertEqual(rule_a.route_id, route_a)
        self.assertEqual(rule_b.company_id, company_b)
        self.assertEqual(rule_b.route_id, route_b)
