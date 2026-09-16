# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.deltatech_expenses.tests.test_expenses import TestExpenses


@tagged("post_install", "-at_install")
class TestExpensesHrBridge(TestExpenses):
    """Testele punții hr.expense <-> deltatech.expenses.deduction. Fixture-urile (companie,
    jurnale, conturi, taxe, angajat, furnizor) sunt cele din TestExpenses (deltatech_expenses)."""

    def test_import_hr_expenses_into_deduction(self):
        """Wizard-ul preia cheltuielile hr.expense eligibile în linii de decont și le leagă."""
        deduction = self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": self.employee.id,
                "advance": 0.0,
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
                "journal_diem_id": self.diary_journal.id,
                "account_diem_id": self.acc_exp.id,
            }
        )
        product = self.env["product.product"].create(
            {"name": "Cheltuiala HR", "can_be_expensed": True, "type": "consu"}
        )
        expense = self.env["hr.expense"].create(
            {
                "name": "Masa de protocol",
                "employee_id": self.employee.id,
                "product_id": product.id,
                "total_amount_currency": 121.0,
                "tax_ids": [(6, 0, [self.tax_incl_21.id])],
                "account_id": self.acc_exp.id,
            }
        )
        # facem cheltuiala eligibilă (aprobată), fără notă contabilă proprie
        expense.approval_state = "approved"
        self.assertIn(expense, deduction._eligible_hr_expenses())

        wizard = (
            self.env["deltatech.expenses.import.hr"].with_context(default_expenses_deduction_id=deduction.id).create({})
        )
        self.assertIn(expense, wizard.expense_ids)
        wizard.action_import()

        # s-a creat o linie și cheltuiala este legată de decont
        self.assertEqual(len(deduction.expenses_line_ids), 1)
        line = deduction.expenses_line_ids
        self.assertEqual(line.name, expense.name)
        # TVA inclus => în linie intră brutul; subtotalul rămâne netul
        self.assertAlmostEqual(line.amount, 121.0, places=2)
        self.assertAlmostEqual(line.price_subtotal, 100.0, places=2)
        self.assertAlmostEqual(line.tax_amount, 21.0, places=2)
        self.assertEqual(line.tax_ids, self.tax_incl_21)
        self.assertEqual(expense.expenses_deduction_id, deduction)
        self.assertEqual(line.hr_expense_id, expense)
        # nu mai este eligibilă a doua oară
        self.assertNotIn(expense, deduction._eligible_hr_expenses())

        # ștergerea liniei eliberează cheltuiala (redevine eligibilă)
        line.unlink()
        self.assertFalse(expense.expenses_deduction_id)
        self.assertIn(expense, deduction._eligible_hr_expenses())

    def test_import_non_price_include_tax(self):
        """La import, o cheltuială cu TVA 'pe deasupra' (non-price-include) este mapată corect:
        subtotalul liniei = netul, TVA-ul = TVA-ul cheltuielii, totalul = brutul."""
        tax_excl = self.env["account.tax"].create(
            {
                "name": "TVA 21 excl",
                "amount": 21.0,
                "amount_type": "percent",
                "price_include_override": "tax_excluded",
                "type_tax_use": "purchase",
                "company_id": self.company.id,
                "tax_group_id": self.tax_group.id,
                "country_id": self.ro_country.id,
            }
        )
        self.assertFalse(tax_excl.price_include)

        deduction = self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": self.employee.id,
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
                "journal_diem_id": self.diary_journal.id,
                "account_diem_id": self.acc_exp.id,
            }
        )
        product = self.env["product.product"].create({"name": "Cheltuiala", "can_be_expensed": True, "type": "consu"})
        expense = self.env["hr.expense"].create(
            {
                "name": "Servicii",
                "employee_id": self.employee.id,
                "product_id": product.id,
                "total_amount_currency": 121.0,  # brut (TVA inclus în total_amount)
                "tax_ids": [(6, 0, tax_excl.ids)],
                "account_id": self.acc_exp.id,
            }
        )
        # cu TVA 'pe deasupra', hr.expense desface brutul: net 100 + TVA 21
        self.assertAlmostEqual(expense.untaxed_amount, 100.0, places=2)
        self.assertAlmostEqual(expense.tax_amount, 21.0, places=2)

        # eligibilă (aprobată), fără notă contabilă proprie — cerință re-validată de _import_hr_expenses
        expense.approval_state = "approved"
        deduction._import_hr_expenses(expense)
        line = deduction.expenses_line_ids
        self.assertAlmostEqual(line.amount, 100.0, places=2)  # netul, nu brutul
        self.assertAlmostEqual(line.price_subtotal, 100.0, places=2)
        self.assertAlmostEqual(line.tax_amount, 21.0, places=2)
        # totalul recompus pe decont = brutul cheltuielii (fără umflare)
        self.assertAlmostEqual(deduction.amount_vouchers, 121.0, places=2)

    def test_import_multiple_hr_expenses_from_list(self):
        """Din lista de cheltuieli: mai multe cheltuieli selectate sunt trimise într-un decont ales."""
        deduction = self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": self.employee.id,
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
                "journal_diem_id": self.diary_journal.id,
                "account_diem_id": self.acc_exp.id,
            }
        )
        product = self.env["product.product"].create({"name": "Cheltuiala", "can_be_expensed": True, "type": "consu"})
        expenses = self.env["hr.expense"]
        for label, amount in (("Cazare", 200.0), ("Transport", 150.0), ("Masa", 90.0)):
            expenses |= self.env["hr.expense"].create(
                {
                    "name": label,
                    "employee_id": self.employee.id,
                    "product_id": product.id,
                    "total_amount_currency": amount,
                    "account_id": self.acc_exp.id,
                }
            )
        expenses.approval_state = "approved"

        # simulează acțiunea contextuală din lista hr.expense (active_model + active_ids)
        wizard = (
            self.env["deltatech.expenses.import.hr"]
            .with_context(active_model="hr.expense", active_ids=expenses.ids)
            .create({})
        )
        self.assertEqual(wizard.employee_id, self.employee)
        self.assertEqual(wizard.expense_ids, expenses)
        wizard.expenses_deduction_id = deduction.id  # utilizatorul alege decontul țintă
        wizard.action_import()

        self.assertEqual(len(deduction.expenses_line_ids), 3)
        self.assertEqual(expenses.mapped("expenses_deduction_id"), deduction)

    def test_invalidate_frees_imported_hr_expense(self):
        """La invalidarea decontului, liniile importate din hr.expense se șterg și cheltuielile
        sunt eliberate (redevin disponibile pentru fluxul standard / o nouă preluare)."""
        deduction = self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": self.employee.id,
                "advance": 200.0,
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
                "journal_diem_id": self.diary_journal.id,
                "account_diem_id": self.acc_exp.id,
            }
        )
        deduction.validate_advance()
        product = self.env["product.product"].create(
            {"name": "Cheltuiala HR", "can_be_expensed": True, "type": "consu"}
        )
        expense = self.env["hr.expense"].create(
            {
                "name": "Cazare delegație",
                "employee_id": self.employee.id,
                "product_id": product.id,
                "total_amount_currency": 121.0,
                "tax_ids": [(6, 0, [self.tax_21.id])],
                "account_id": self.acc_exp.id,
                "vendor_id": self.supplier.id,
            }
        )
        expense.approval_state = "approved"
        deduction._import_hr_expenses(expense)
        self.assertEqual(expense.expenses_deduction_id, deduction)
        self.assertTrue(deduction.expenses_line_ids.filtered("hr_expense_id"))

        deduction.validate_expenses()
        self.assertEqual(deduction.state, "done")

        deduction.invalidate_expenses()
        self.assertEqual(deduction.state, "draft")
        # linia importată a fost ștearsă, iar cheltuiala este eliberată și redevine eligibilă
        self.assertFalse(deduction.expenses_line_ids.filtered("hr_expense_id"))
        self.assertFalse(expense.expenses_deduction_id)
        self.assertIn(expense, deduction._eligible_hr_expenses())

    def test_hr_expense_linked_to_deduction_not_posted(self):
        """O cheltuială hr.expense legată de un decont nu generează note contabile standard."""
        expenses = self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": self.employee.id,
                "advance": 100.0,
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
                "journal_diem_id": self.diary_journal.id,
                "account_diem_id": self.acc_exp.id,
            }
        )
        product = self.env["product.product"].create({"name": "Cheltuiala", "can_be_expensed": True, "type": "consu"})
        hr_exp = self.env["hr.expense"].create(
            {
                "name": "Cazare hr",
                "employee_id": self.employee.id,
                "product_id": product.id,
                "total_amount_currency": 100.0,
                "expenses_deduction_id": expenses.id,
            }
        )
        result = hr_exp.action_post()
        self.assertFalse(result)
        self.assertFalse(hr_exp.account_move_id)
        self.assertNotIn(hr_exp.state, ("posted", "paid"))

    def test_import_hr_expenses_rejects_mismatched_employee(self):
        """_import_hr_expenses respinge o cheltuială a altui angajat chiar dacă i se dă direct
        (re-validare server-side, tichet POPVAL-COS, pct. 4)."""
        other_employee = self.env["hr.employee"].create({"name": "Alt Angajat"})
        deduction = self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": self.employee.id,
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
                "journal_diem_id": self.diary_journal.id,
                "account_diem_id": self.acc_exp.id,
            }
        )
        product = self.env["product.product"].create({"name": "Cheltuiala", "can_be_expensed": True, "type": "consu"})
        foreign_expense = self.env["hr.expense"].create(
            {
                "name": "Cheltuiala altui angajat",
                "employee_id": other_employee.id,
                "product_id": product.id,
                "total_amount_currency": 50.0,
                "account_id": self.acc_exp.id,
            }
        )
        foreign_expense.approval_state = "approved"

        with self.assertRaises(UserError):
            deduction._import_hr_expenses(foreign_expense)
        self.assertFalse(deduction.expenses_line_ids)
        self.assertFalse(foreign_expense.expenses_deduction_id)

    def test_import_hr_expenses_rejects_when_deduction_not_open(self):
        """_import_hr_expenses respinge preluarea într-un decont deja Finalizat/Anulat, nu doar
        la deschiderea wizard-ului (tichet POPVAL-COS, runda 2)."""
        deduction = self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": self.employee.id,
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
                "journal_diem_id": self.diary_journal.id,
                "account_diem_id": self.acc_exp.id,
            }
        )
        deduction.validate_advance()
        deduction.validate_expenses()
        self.assertEqual(deduction.state, "done")

        product = self.env["product.product"].create({"name": "Cheltuiala", "can_be_expensed": True, "type": "consu"})
        expense = self.env["hr.expense"].create(
            {
                "name": "Cheltuiala tarzie",
                "employee_id": self.employee.id,
                "product_id": product.id,
                "total_amount_currency": 50.0,
                "account_id": self.acc_exp.id,
            }
        )
        expense.approval_state = "approved"

        with self.assertRaises(UserError):
            deduction._import_hr_expenses(expense)
        self.assertFalse(expense.expenses_deduction_id)
