# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestExpenses(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Basic company settings
        cls.company = cls.env.company
        cash_journal = cls.env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", cls.env.company.id)], limit=1
        )
        # Create accounts: Cash (5311), Cash advances (542), Expense (6xx)

        if not cash_journal:
            cash_journal = cls.env["account.journal"].create(
                {
                    "name": "Cash",
                    "code": "CASH",
                    "type": "cash",
                    "company_id": cls.company.id,
                }
            )

        cls.acc_cash = cash_journal.default_account_id

        cls.acc_542 = cls.env["account.account"].create(
            {
                "name": "Cash Advances",
                "code": "542TEST",
                "account_type": "asset_current",
            }
        )
        cls.acc_exp = cls.env["account.account"].create(
            {
                "name": "Expenses 6xx",
                "code": "625TEST",
                "account_type": "expense",
            }
        )
        cls.acc_payable = cls.env["account.account"].create(
            {
                "name": "Furnizori",
                "code": "401TEST",
                "account_type": "liability_payable",
                "reconcile": True,
            }
        )
        # Journals: cash journal uses cash account; advance/expense journal uses 542
        cls.cash_journal = cash_journal
        cls.adv_journal = cls.env["account.journal"].create(
            {
                "name": "Adv J",
                "code": "ADJ",
                "type": "general",
                "default_account_id": cls.acc_542.id,
                "company_id": cls.company.id,
            }
        )
        cls.diary_journal = cls.env["account.journal"].create(
            {
                "name": "Diem J",
                "code": "DMJ",
                "type": "general",
                "default_account_id": cls.acc_exp.id,
                "company_id": cls.company.id,
            }
        )
        # Purchase journal for vouchers
        cls.purchase_journal = cls.env["account.journal"].create(
            {
                "name": "Purch J",
                "code": "PUJ",
                "type": "purchase",
                "company_id": cls.company.id,
            }
        )
        # asigurăm țara fiscală RO (postarea moves verifică compatibilitatea taxă ↔ țară companie)
        cls.ro_country = cls.env.ref("base.ro")
        if cls.company.country_id != cls.ro_country:
            cls.company.country_id = cls.ro_country.id

        # Tax 21% price included
        tax_group = cls.env["account.tax.group"].search([("company_id", "=", cls.company.id)], limit=1)
        if not tax_group:
            tax_group = cls.env["account.tax.group"].create({"name": "TVA", "company_id": cls.company.id})
        cls.tax_incl_21 = cls.env["account.tax"].create(
            {
                "name": "TVA 21 incl",
                "amount": 21.0,
                "amount_type": "percent",
                "price_include": True,
                "type_tax_use": "purchase",
                "company_id": cls.company.id,
                "tax_group_id": tax_group.id,
                "country_id": cls.ro_country.id,
            }
        )
        # Partners
        cls.employee_partner = cls.env["res.partner"].create({"name": "Angajat X"})
        cls.employee = cls.env["hr.employee"].create({"name": "Angajat X", "work_contact_id": cls.employee_partner.id})
        cls.supplier = cls.env["res.partner"].create({"name": "Furnizor Y", "is_company": True})
        cls.supplier.property_account_payable_id = cls.acc_payable.id

    def _lines_for_expenses(self, expenses):
        return self.env["account.move.line"].search([("move_id.expenses_deduction_id", "=", expenses.id)])

    def test_employee_deduction_smart_button(self):
        """Fișa angajatului numără deconturile și acțiunea le filtrează."""
        self.assertEqual(self.employee.expenses_deduction_count, 0)
        self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": self.employee.id,
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
                "journal_diem_id": self.diary_journal.id,
                "account_diem_id": self.acc_exp.id,
            }
        )
        self.employee.invalidate_recordset(["expenses_deduction_count"])
        self.assertEqual(self.employee.expenses_deduction_count, 1)
        action = self.employee.action_open_expenses_deductions()
        self.assertEqual(action["res_model"], "deltatech.expenses.deduction")
        self.assertIn(("employee_id", "=", self.employee.id), action["domain"])

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
                "total_amount": 121.0,
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
        self.assertAlmostEqual(line.amount, 121.0, places=2)
        self.assertEqual(line.tax_ids, self.tax_incl_21)
        self.assertEqual(expense.expenses_deduction_id, deduction)
        self.assertEqual(line.hr_expense_id, expense)
        # nu mai este eligibilă a doua oară
        self.assertNotIn(expense, deduction._eligible_hr_expenses())

        # ștergerea liniei eliberează cheltuiala (redevine eligibilă)
        line.unlink()
        self.assertFalse(expense.expenses_deduction_id)
        self.assertIn(expense, deduction._eligible_hr_expenses())

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
                    "total_amount": amount,
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
                "total_amount": 100.0,
                "expenses_deduction_id": expenses.id,
            }
        )
        result = hr_exp.action_post()
        self.assertFalse(result)
        self.assertFalse(hr_exp.account_move_id)
        self.assertNotIn(hr_exp.state, ("posted", "paid"))

    def test_advance_without_partner_internal(self):
        """Angajat fără work_contact_id: notele de avans se generează fără partener (interne)."""
        employee_no_partner = self.env["hr.employee"].create({"name": "Angajat Intern"})
        # Odoo atribuie automat un work_contact_id la creare; îl golim ca să testăm cazul intern
        employee_no_partner.work_contact_id = False
        expenses = self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": employee_no_partner.id,
                "advance": 500.0,
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
                "journal_diem_id": self.diary_journal.id,
                "account_diem_id": self.acc_exp.id,
            }
        )
        self.assertFalse(expenses.partner_id)
        # validarea nu trebuie să arunce eroare doar pentru lipsa partenerului
        expenses.validate_advance()
        self.assertEqual(expenses.state, "advance")
        adv_lines = self._lines_for_expenses(expenses).filtered(lambda l: l.move_id.ref == expenses.number)
        self.assertTrue(adv_lines)
        self.assertFalse(any(adv_lines.mapped("partner_id")))

    def test_full_flow_advance_expense_refund_and_zero_542(self):
        # Create expenses document with advance 1000
        expenses = self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": self.employee.id,
                "advance": 1000.0,
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
                "journal_diem_id": self.diary_journal.id,
                "account_diem_id": self.acc_exp.id,
            }
        )
        # partner_id (related stored) se rezolvă din work_contact_id al angajatului
        self.assertEqual(expenses.partner_id, self.employee_partner)

        # onchange date sets expense date if not provided
        expenses.onchange_date_advance()
        self.assertEqual(expenses.date_expense, expenses.date_advance)

        # Validate advance: creates a move debiting 542 and crediting cash
        expenses.validate_advance()
        self.assertEqual(expenses.state, "advance")
        adv_lines = self._lines_for_expenses(expenses).filtered(lambda l: l.move_id.ref == expenses.number)
        self.assertTrue(adv_lines)
        # Ensure 542 debit 1000 and cash credit 1000 exist
        self.assertAlmostEqual(
            sum(adv_lines.filtered(lambda l: l.account_id.id == self.acc_542.id).mapped("debit")), 1000.0, places=2
        )
        self.assertAlmostEqual(
            sum(adv_lines.filtered(lambda l: l.account_id.id == self.acc_cash.id).mapped("credit")), 1000.0, places=2
        )

        # Add two expense lines totaling 800 RON, price includes 19% VAT
        self.env["deltatech.expenses.deduction.line"].create(
            {
                "expenses_deduction_id": expenses.id,
                "name": "Cazare",
                "amount": 500.0,
                "tax_ids": [(6, 0, [self.tax_incl_21.id])],
                "expense_account_id": self.acc_exp.id,
                "partner_id": self.supplier.id,
            }
        )
        self.env["deltatech.expenses.deduction.line"].create(
            {
                "expenses_deduction_id": expenses.id,
                "name": "Transport",
                "amount": 300.0,
                "tax_ids": [(6, 0, [self.tax_incl_21.id])],
                "expense_account_id": self.acc_exp.id,
                "partner_id": self.supplier.id,
            }
        )

        # Check computed amounts on lines and on document
        expenses.invalidate_recordset()
        net_total = sum(expenses.expenses_line_ids.mapped("price_subtotal"))
        tax_total = sum(expenses.expenses_line_ids.mapped("tax_amount"))
        # Be tolerant across environments: ensure internal consistency (net + tax equals vouchers amount)
        self.assertAlmostEqual(net_total + tax_total, expenses.amount_vouchers, places=2)
        self.assertGreaterEqual(tax_total, 0.0)
        # Difference is computed against the advance actually given
        self.assertAlmostEqual(expenses.difference, expenses.amount_vouchers - 1000.0, places=2)

        # Validare decont: generează chitanțe (in_receipt), note de decontare Dr 401 = Cr 542,
        # reconciliază datoriile către furnizor și înregistrează diferența
        expenses.validate_expenses()
        self.assertEqual(expenses.state, "done")

        # contul 542 se închide pentru acest decont (debit = credit)
        all_lines = self._lines_for_expenses(expenses)
        lines_542 = all_lines.filtered(lambda l: l.account_id.id == self.acc_542.id)
        debit_542 = sum(lines_542.mapped("debit"))
        credit_542 = sum(lines_542.mapped("credit"))
        self.assertAlmostEqual(debit_542, credit_542, places=2)
        self.assertGreater(debit_542, 0.0)

        # chitanțele furnizor sunt complet decontate din avans (fără sold rămas)
        vouchers = expenses.voucher_ids
        self.assertTrue(vouchers)
        self.assertTrue(all(v.payment_state in ("paid", "in_payment", "reversed") for v in vouchers))

        # Invalidarea readuce decontul în Ciornă și șterge notele generate
        expenses.invalidate_expenses()
        self.assertEqual(expenses.state, "draft")
        self.assertFalse(self._lines_for_expenses(expenses))
