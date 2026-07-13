# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields
from odoo.exceptions import AccessError, UserError
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
        # asigurăm țara fiscală RO (postarea moves verifică compatibilitatea taxă ↔ țară companie).
        # account_fiscal_country_id e setat EXPLICIT: în CI compania nu are plan de conturi RO, deci
        # nu derivă singură din country_id.
        cls.ro_country = cls.env.ref("base.ro")
        cls.company.write({"country_id": cls.ro_country.id, "account_fiscal_country_id": cls.ro_country.id})

        # grup de taxe cu aceeași țară ca taxele (validare account.tax: tax.country_id == group.country_id)
        cls.tax_group = cls.env["account.tax.group"].create(
            {"name": "TVA Test", "company_id": cls.company.id, "country_id": cls.ro_country.id}
        )
        # Taxa standard a modulului: TVA „pe deasupra" (price-excluded) — voucher-ul adaugă TVA peste net
        cls.tax_21 = cls.env["account.tax"].create(
            {
                "name": "TVA 21",
                "amount": 21.0,
                "amount_type": "percent",
                "price_include_override": "tax_excluded",
                "type_tax_use": "purchase",
                "company_id": cls.company.id,
                "tax_group_id": cls.tax_group.id,
                "country_id": cls.ro_country.id,
            }
        )
        # Taxă cu TVA inclus (pentru testarea ramurii de import „brut")
        cls.tax_incl_21 = cls.env["account.tax"].create(
            {
                "name": "TVA 21 incl",
                "amount": 21.0,
                "amount_type": "percent",
                "price_include_override": "tax_included",
                "type_tax_use": "purchase",
                "company_id": cls.company.id,
                "tax_group_id": cls.tax_group.id,
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

    def test_supplier_payment_reconciles_open_bill(self):
        """Linia 'supplier_payment' stinge o factură furnizor deschisă din avans (reconciliere)."""
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.supplier.id,
                "invoice_date": fields.Date.today(),
                "journal_id": self.purchase_journal.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {"name": "Marfă", "price_unit": 100.0, "account_id": self.acc_exp.id, "tax_ids": [(6, 0, [])]},
                    )
                ],
            }
        )
        bill.action_post()
        self.assertEqual(bill.payment_state, "not_paid")

        deduction = self.env["deltatech.expenses.deduction"].create(
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
        deduction.validate_advance()
        self.env["deltatech.expenses.deduction.line"].create(
            {
                "expenses_deduction_id": deduction.id,
                "name": "Plată furnizor",
                "amount": 100.0,
                "type": "supplier_payment",
                "partner_id": self.supplier.id,
                "expense_account_id": self.acc_exp.id,
            }
        )
        deduction.validate_expenses()
        self.assertEqual(deduction.state, "done")
        # factura furnizor este stinsă din avans, iar contul 542 se închide
        self.assertIn(bill.payment_state, ("paid", "in_payment", "reversed"))
        lines_542 = self._lines_for_expenses(deduction).filtered(lambda l: l.account_id.id == self.acc_542.id)
        self.assertAlmostEqual(sum(lines_542.mapped("debit")), sum(lines_542.mapped("credit")), places=2)

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
                "tax_ids": [(6, 0, [self.tax_21.id])],
                "expense_account_id": self.acc_exp.id,
                "partner_id": self.supplier.id,
            }
        )
        self.env["deltatech.expenses.deduction.line"].create(
            {
                "expenses_deduction_id": expenses.id,
                "name": "Transport",
                "amount": 300.0,
                "tax_ids": [(6, 0, [self.tax_21.id])],
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

    def test_advance_settlement_542_line_uses_employee_partner(self):
        """Linia de 542 din decontarea avansului rămâne pe partenerul angajatului;
        doar linia de 401 e pe furnizor (tichet POPVAL-COS, pct. 1)."""
        deduction = self.env["deltatech.expenses.deduction"].create(
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
        deduction.validate_advance()
        self.env["deltatech.expenses.deduction.line"].create(
            {
                "expenses_deduction_id": deduction.id,
                "name": "Plată furnizor",
                "amount": 100.0,
                "type": "supplier_payment",
                "partner_id": self.supplier.id,
                "expense_account_id": self.acc_exp.id,
            }
        )
        deduction.validate_expenses()

        settlement_lines = self._lines_for_expenses(deduction).filtered(lambda l: l.name == "Decontare avans")
        lines_401 = settlement_lines.filtered(lambda l: l.account_id.id == self.acc_payable.id)
        lines_542 = settlement_lines.filtered(lambda l: l.account_id.id == self.acc_542.id)
        self.assertTrue(lines_401)
        self.assertTrue(lines_542)
        self.assertEqual(set(lines_401.mapped("partner_id.id")), {self.supplier.id})
        self.assertEqual(set(lines_542.mapped("partner_id.id")), {self.employee_partner.id})

    def test_validate_advance_rejects_second_call(self):
        """Reapelarea validate_advance peste un decont deja în Avans e respinsă (dublă contabilizare)."""
        deduction = self.env["deltatech.expenses.deduction"].create(
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
        deduction.validate_advance()
        with self.assertRaises(UserError):
            deduction.validate_advance()

    def test_validate_expenses_rejects_second_call(self):
        """Reapelarea validate_expenses peste un decont deja Finalizat e respinsă."""
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
        with self.assertRaises(UserError):
            deduction.validate_expenses()

    def test_invalidate_requires_done_state(self):
        """invalidate_expenses respinge un decont care nu e Finalizat."""
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
        with self.assertRaises(UserError):
            deduction.invalidate_expenses()

    def test_reconcile_supplier_payment_scoped_to_company(self):
        """O factură a aceluiași furnizor dintr-o altă companie NU este reconciliată din avans
        (tichet POPVAL-COS, pct. 5)."""
        company2 = self.env["res.company"].create({"name": "Compania 2 Test"})
        # contul devine utilizabil în compania 2: are nevoie de un cod propriu per companie
        self.acc_payable.write(
            {
                "company_ids": [(4, company2.id)],
                "code_mapping_ids": [(0, 0, {"company_id": company2.id, "code": "401TEST2"})],
            }
        )
        self.acc_exp.write(
            {
                "company_ids": [(4, company2.id)],
                "code_mapping_ids": [(0, 0, {"company_id": company2.id, "code": "625TEST2"})],
            }
        )
        purchase_journal2 = self.env["account.journal"].create(
            {
                "name": "Purch J2",
                "code": "PUJ2",
                "type": "purchase",
                "company_id": company2.id,
            }
        )
        bill_other_company = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.supplier.id,
                "company_id": company2.id,
                "invoice_date": fields.Date.today(),
                "journal_id": purchase_journal2.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Marfă altă companie",
                            "price_unit": 500.0,
                            "account_id": self.acc_exp.id,
                            "tax_ids": [(6, 0, [])],
                        },
                    )
                ],
            }
        )
        bill_other_company.action_post()
        self.assertEqual(bill_other_company.payment_state, "not_paid")

        deduction = self.env["deltatech.expenses.deduction"].create(
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
        deduction.validate_advance()
        self.env["deltatech.expenses.deduction.line"].create(
            {
                "expenses_deduction_id": deduction.id,
                "name": "Plată furnizor",
                "amount": 100.0,
                "type": "supplier_payment",
                "partner_id": self.supplier.id,
                "expense_account_id": self.acc_exp.id,
            }
        )
        deduction.validate_expenses()
        self.assertEqual(deduction.state, "done")

        # factura din compania 2 rămâne neatinsă
        bill_other_company.invalidate_recordset(["payment_state"])
        self.assertEqual(bill_other_company.payment_state, "not_paid")

    def test_validate_expenses_price_include_tax_document_total(self):
        """Pentru taxe TVA inclus, chitanța generată la validate_expenses păstrează totalul brut
        corect — nu doar linia, ci documentul postat în întregime (tichet POPVAL-COS, pct. 2)."""
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
        self.env["deltatech.expenses.deduction.line"].create(
            {
                "expenses_deduction_id": deduction.id,
                "name": "Cazare TVA inclus",
                "amount": 121.0,
                "tax_ids": [(6, 0, [self.tax_incl_21.id])],
                "expense_account_id": self.acc_exp.id,
                "partner_id": self.supplier.id,
            }
        )
        deduction.validate_expenses()

        voucher = deduction.voucher_ids
        self.assertEqual(len(voucher), 1)
        self.assertAlmostEqual(voucher.amount_total, 121.0, places=2)
        self.assertAlmostEqual(voucher.amount_untaxed, 100.0, places=2)
        self.assertAlmostEqual(voucher.amount_tax, 21.0, places=2)

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

    def test_role_separation_advance_and_validate(self):
        """Doar Aprobatorul poate valida avansul; doar Contabilul poate finaliza decontul
        (tichet POPVAL-COS, pct. 6)."""
        plain_user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Angajat Test",
                    "login": "expenses_plain_user_test",
                    "email": "expenses_plain_user_test@example.com",
                    "group_ids": [(6, 0, [self.env.ref("deltatech_expenses.group_expenses_user").id])],
                }
            )
        )
        approver_user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Aprobator Test",
                    "login": "expenses_approver_user_test",
                    "email": "expenses_approver_user_test@example.com",
                    "group_ids": [(6, 0, [self.env.ref("deltatech_expenses.group_expenses_approver").id])],
                }
            )
        )
        accounting_user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Contabil Test",
                    "login": "expenses_accounting_user_test",
                    "email": "expenses_accounting_user_test@example.com",
                    "group_ids": [(6, 0, [self.env.ref("deltatech_expenses.group_expenses_accounting").id])],
                }
            )
        )

        deduction = self.env["deltatech.expenses.deduction"].create(
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

        with self.assertRaises(AccessError):
            deduction.with_user(plain_user).validate_advance()

        deduction.with_user(approver_user).validate_advance()
        self.assertEqual(deduction.state, "advance")
        self.assertEqual(deduction.approved_by_id, approver_user)

        self.env["deltatech.expenses.deduction.line"].create(
            {
                "expenses_deduction_id": deduction.id,
                "name": "Cazare",
                "amount": 100.0,
                "expense_account_id": self.acc_exp.id,
                "partner_id": self.supplier.id,
            }
        )

        with self.assertRaises(AccessError):
            deduction.with_user(approver_user).validate_expenses()

        deduction.with_user(accounting_user).validate_expenses()
        self.assertEqual(deduction.state, "done")
        self.assertEqual(deduction.accounted_by_id, accounting_user)

    def test_default_account_diem_uses_company_ids(self):
        """_default_account_diem caută pe company_ids (many2many), nu pe company_id — altfel
        căutarea eșuează silențios și contul de diurnă nu se completează niciodată (tichet
        POPVAL-COS, runda 2). Companie izolată, ca să nu depindem de ce alte conturi 625% mai
        există în baza de test."""
        company_iso = self.env["res.company"].create({"name": "Diem Test Co"})
        acc_diem_iso = self.env["account.account"].create(
            {
                "name": "Cheltuieli deplasari izolat",
                "code": "625ISO",
                "account_type": "expense",
                "company_ids": [(6, 0, [company_iso.id])],
            }
        )
        result = self.env["deltatech.expenses.deduction"].with_company(company_iso)._default_account_diem()
        self.assertEqual(result, acc_diem_iso)

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

    def test_expenses_line_own_rule_restricts_access(self):
        """Un Angajat nu poate citi direct linia unui decont care nu îi aparține — regulă proprie
        pe modelul de linie, nu doar pe decont (tichet POPVAL-COS, runda 2)."""
        other_employee = self.env["hr.employee"].create({"name": "Alt Angajat Linie"})
        deduction = self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": other_employee.id,
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
                "journal_diem_id": self.diary_journal.id,
                "account_diem_id": self.acc_exp.id,
            }
        )
        line = self.env["deltatech.expenses.deduction.line"].create(
            {
                "expenses_deduction_id": deduction.id,
                "name": "Cazare",
                "amount": 100.0,
                "expense_account_id": self.acc_exp.id,
                "partner_id": self.supplier.id,
            }
        )
        plain_user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Angajat Linie Test",
                    "login": "expenses_line_user_test",
                    "email": "expenses_line_user_test@example.com",
                    "group_ids": [(6, 0, [self.env.ref("deltatech_expenses.group_expenses_user").id])],
                }
            )
        )
        with self.assertRaises(AccessError):
            line.with_user(plain_user).read(["name"])
