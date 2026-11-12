# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from lxml import etree

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMarginColumnsGroup(TransactionCase):
    """The margin and purchase price columns of the order lines follow the
    same group as the margin total of the order."""

    def _line_fields(self, user):
        view = self.env["sale.order"].with_user(user).get_view(view_type="form")
        arch = etree.fromstring(view["arch"])
        names = set()
        for node in arch.xpath("//field[@name='order_line']//list//field | //field[@name='order_line']//form//field"):
            names.add(node.get("name"))
        return names

    def _make_user(self, login, groups):
        return self.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "group_ids": [(6, 0, [self.env.ref(g).id for g in groups])],
            }
        )

    def test_columns_hidden_without_group(self):
        user = self._make_user("margin_no_group", ["sales_team.group_sale_salesman"])
        names = self._line_fields(user)
        for name in ("purchase_price", "margin", "margin_percent"):
            self.assertNotIn(name, names)

    def test_columns_shown_with_group(self):
        user = self._make_user(
            "margin_with_group",
            ["sales_team.group_sale_salesman", "deltatech_sale_margin.group_sale_margin"],
        )
        names = self._line_fields(user)
        for name in ("purchase_price", "margin", "margin_percent"):
            self.assertIn(name, names)
