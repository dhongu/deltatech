from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleTeamAccess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.team_manager = new_test_user(
            cls.env, login="dt_team_manager", groups="base.group_user,deltatech_sale_team.group_sale_team_manager"
        )
        cls.salesman = new_test_user(
            cls.env, login="dt_salesman", groups="base.group_user,sales_team.group_sale_salesman"
        )
        cls.sale_manager = new_test_user(
            cls.env, login="dt_sale_manager", groups="base.group_user,sales_team.group_sale_manager"
        )
        cls.other_user = new_test_user(
            cls.env, login="dt_other", groups="base.group_user,sales_team.group_sale_salesman"
        )

        cls.team_a = cls.env["crm.team"].create({"name": "DT Team A"})
        cls.team_b = cls.env["crm.team"].create({"name": "DT Team B"})
        cls.env["crm.team.member"].create({"crm_team_id": cls.team_a.id, "user_id": cls.team_manager.id})

        cls.partner = cls.env["res.partner"].create({"name": "DT Customer"})
        cls.partner_other = cls.env["res.partner"].create({"name": "DT Other Customer", "user_id": cls.other_user.id})

        cls.order_a = cls.env["sale.order"].create(
            {"partner_id": cls.partner.id, "team_id": cls.team_a.id, "user_id": cls.other_user.id}
        )
        cls.order_b = cls.env["sale.order"].create(
            {"partner_id": cls.partner.id, "team_id": cls.team_b.id, "user_id": cls.other_user.id}
        )

    def test_team_manager_sees_team_orders(self):
        self.assertEqual(self.team_manager.sale_team_id, self.team_a)
        orders = self.env["sale.order"].with_user(self.team_manager).search([("id", "in", self.orders.ids)])
        self.assertEqual(orders, self.order_a)
        lines_domain = self.env["sale.order.line"].with_user(self.team_manager)._access_domain("read")
        self.assertFalse(lines_domain.is_false())

    def test_salesman_does_not_see_other_orders(self):
        orders = self.env["sale.order"].with_user(self.salesman).search([("id", "in", self.orders.ids)])
        self.assertFalse(orders)

    def test_own_sales_team_only(self):
        teams = self.env["crm.team"].with_user(self.team_manager).search([("id", "in", self.teams.ids)])
        self.assertEqual(teams, self.team_a)
        teams = self.env["crm.team"].with_user(self.salesman).search([("id", "in", self.teams.ids)])
        self.assertEqual(teams, self.teams)
        teams = self.env["crm.team"].with_user(self.sale_manager).search([("id", "in", self.teams.ids)])
        self.assertEqual(teams, self.teams)

    def test_personal_partners(self):
        partners = self.partner | self.partner_other
        visible = self.env["res.partner"].with_user(self.salesman).search([("id", "in", partners.ids)])
        self.assertEqual(visible, self.partner)
        visible = self.env["res.partner"].with_user(self.sale_manager).search([("id", "in", partners.ids)])
        self.assertEqual(visible, partners)

    @property
    def orders(self):
        return self.order_a | self.order_b

    @property
    def teams(self):
        return self.team_a | self.team_b
