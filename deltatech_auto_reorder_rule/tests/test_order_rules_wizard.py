# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestOrderRulesWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Wizard rule product", "type": "consu", "is_storable": True}
        )
        warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.location = cls.env["stock.location"].create(
            {"name": "Wizard shelf", "usage": "internal", "location_id": warehouse.lot_stock_id.id}
        )

    def test_do_create_rules(self):
        """REORDER-004: the wizard must not send the removed qty_multiple field."""
        wizard = (
            self.env["order.rules.details.wizard"]
            .with_context(active_id=self.product.product_tmpl_id.id)
            .create(
                {
                    "min_quantity": 5,
                    "max_quantity": 20,
                    "trigger": "auto",
                    "stock_location_ids": [(6, 0, self.location.ids)],
                }
            )
        )
        wizard.do_create()
        rule = self.env["stock.warehouse.orderpoint"].search(
            [("product_id", "=", self.product.id), ("location_id", "=", self.location.id)]
        )
        self.assertEqual(len(rule), 1)
        self.assertRecordValues(
            rule,
            [{"product_min_qty": 5, "product_max_qty": 20, "trigger": "auto", "location_id": self.location.id}],
        )
