from odoo.tests.common import TransactionCase


class TestCrmTeamAndSaleOrder(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a test warehouse
        self.warehouse = self.env["stock.warehouse"].create({"name": "Test Warehouse", "code": "TW"})

        # Create a CRM team
        self.crm_team = self.env["crm.team"].create(
            {
                "name": "Test Sales Team",
                "team_type": "sales",
                "warehouse_id": self.warehouse.id,
            }
        )

        # Create a test partner
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})

        # Create a sale order
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "team_id": self.crm_team.id,
            }
        )

    def test_team_type_and_warehouse(self):
        # Check CRM team creation and default values
        self.assertEqual(self.crm_team.team_type, "sales", "Default team type should be 'sales'")
        self.assertEqual(self.crm_team.warehouse_id, self.warehouse, "The warehouse should be assigned correctly")

    def test_onchange_team_id(self):
        # Check if the onchange method correctly updates the warehouse
        self.sale_order.on_change_team_id()
        self.assertEqual(
            self.sale_order.warehouse_id,
            self.crm_team.warehouse_id,
            "The warehouse should match the CRM team's warehouse",
        )

    def test_action_sale_order_button(self):
        # Check the action_sale_order_button method
        action = self.crm_team.action_sale_order_button()
        self.assertEqual(action["domain"], [("state", "=", "sent")], "The domain should filter by sent quotations")
        self.assertEqual(
            action["context"]["search_default_team_id"],
            [self.crm_team.id],
            "The context should set the default team ID",
        )

    def test_show_products(self):
        # Check the show_products method
        action = self.crm_team.show_products()
        self.assertEqual(action["context"]["warehouse"], self.warehouse.id, "The context should set the warehouse ID")
        self.assertEqual(
            action["context"]["search_default_real_stock_available"],
            1,
            "The context should enable the real stock available filter",
        )

    def test_show_validated_quotations(self):
        # Check the show_validated_quotations method
        action = self.crm_team.show_validated_quotations()
        self.assertEqual(action["domain"], [("state", "=", "sent")], "The domain should filter by sent quotations")
        self.assertEqual(
            action["context"]["search_default_team_id"],
            [self.crm_team.id],
            "The context should set the default team ID",
        )
        self.assertEqual(
            action["context"]["default_team_id"], self.crm_team.id, "The context should set the default team ID"
        )
