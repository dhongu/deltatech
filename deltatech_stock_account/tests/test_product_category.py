from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestProductCategoryPropagation(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.valuation_account = cls.copy_account(cls.company_data["default_account_assets"])
        cls.expense_account = cls.company_data["default_account_expense"]
        cls.income_account = cls.company_data["default_account_revenue"]
        cls.price_diff_account = cls.copy_account(cls.expense_account)
        cls.stock_journal = cls.company_data["default_journal_misc"]
        cls.parent = cls.env["product.category"].create({"name": "Parent"})
        cls.child = cls.env["product.category"].create({"name": "Child", "parent_id": cls.parent.id})
        cls.grandchild = cls.env["product.category"].create({"name": "Grandchild", "parent_id": cls.child.id})

    def _parent_values(self):
        return {
            "property_price_difference_account_id": self.price_diff_account.id,
            "property_account_expense_categ_id": self.expense_account.id,
            "property_account_income_categ_id": self.income_account.id,
            "property_stock_journal": self.stock_journal.id,
            "property_cost_method": "average",
            "property_valuation": "real_time",
        }

    def _assert_accounts(self, categories, check_journal=True):
        for categ in categories:
            self.assertEqual(categ.property_stock_valuation_account_id, self.valuation_account)
            self.assertEqual(categ.property_price_difference_account_id, self.price_diff_account)
            self.assertEqual(categ.property_account_expense_categ_id, self.expense_account)
            self.assertEqual(categ.property_account_income_categ_id, self.income_account)
            if check_journal:
                self.assertEqual(categ.property_stock_journal, self.stock_journal)
            self.assertEqual(categ.property_cost_method, "average")
            self.assertEqual(categ.property_valuation, "real_time")

    def test_write_valuation_account_propagates_to_descendants(self):
        self.parent.write(self._parent_values())
        self.parent.write({"property_stock_valuation_account_id": self.valuation_account.id})
        self._assert_accounts(self.child | self.grandchild)

    def test_propagate_action(self):
        self.parent.write(dict(self._parent_values(), property_stock_valuation_account_id=self.valuation_account.id))
        self.child.write({"property_cost_method": "fifo"})
        self.parent.propagate_account()
        self._assert_accounts(self.child | self.grandchild)

    def test_onchange_parent_copies_accounts(self):
        self.parent.write(dict(self._parent_values(), property_stock_valuation_account_id=self.valuation_account.id))
        with Form(self.env["product.category"]) as form:
            form.name = "New child"
            form.parent_id = self.parent
        # The stock journal is not on the Odoo 19 category form, so the client never saves it
        self._assert_accounts(form.record, check_journal=False)
