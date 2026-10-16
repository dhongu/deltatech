# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAnalyticLineSearchView(TransactionCase):
    def _search_arch(self, xmlid):
        view = self.env.ref(xmlid)
        return self.env["account.analytic.line"].get_view(view.id, "search")["arch"]

    def test_groupings_on_the_accounting_search(self):
        arch = self._search_arch("account.view_account_analytic_line_filter_inherit_account")
        self.assertIn("group_team", arch)
        self.assertIn("group_prod_categ", arch)

    def test_base_search_stays_clean(self):
        """Căutarea din analytic e moștenită primary de raportul de pontaje (hr_timesheet),
        care n-are team_id: grupările de aici ar bloca instalarea pontajelor."""
        arch = self._search_arch("analytic.view_account_analytic_line_filter")
        self.assertNotIn("team_id", arch)
        self.assertNotIn("product_category_id", arch)
