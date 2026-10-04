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
        cls.supplier = cls.env["res.partner"].create({"name": "Furnizor Y"})
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

    def test_journal_entries_dr_cr_full_scenario(self):
        """Notele Dr/Cr complete pentru un decont cu avans, chitanțe (TVA pe deasupra și TVA
        inclus), plată directă furnizor și diurnă — aceleași valori ca în 19.0 (referința
        migrării 19 → 20)."""
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.supplier.id,
                "invoice_date": "2026-01-10",
                "date": "2026-01-10",
                "journal_id": self.purchase_journal.id,
                "invoice_line_ids": [
                    (0, 0, {"name": "Marfă", "price_unit": 150.0, "account_id": self.acc_exp.id, "tax_ids": []})
                ],
            }
        )
        bill.action_post()
        deduction = self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": "2026-01-15",
                "date_expense": "2026-01-20",
                "employee_id": self.employee.id,
                "advance": 1000.0,
                "days": 2,
                "diem": 42.5,
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
                "journal_diem_id": self.diary_journal.id,
                "account_diem_id": self.acc_exp.id,
            }
        )
        deduction.validate_advance()
        line_vals = [
            ("Cazare", 500.0, self.tax_21, "expenses"),
            ("Masa TVA inclus", 121.0, self.tax_incl_21, "expenses"),
            ("Plată furnizor", 150.0, self.env["account.tax"], "supplier_payment"),
        ]
        for name, amount, taxes, line_type in line_vals:
            self.env["deltatech.expenses.deduction.line"].create(
                {
                    "expenses_deduction_id": deduction.id,
                    "date": "2026-01-18",
                    "name": name,
                    "amount": amount,
                    "tax_ids": [(6, 0, taxes.ids)],
                    "type": line_type,
                    "partner_id": self.supplier.id,
                    "expense_account_id": self.acc_exp.id,
                }
            )
        # 605 + 121 + 150 + 2 * 42.5 = 961 → diferență -39 (de restituit)
        self.assertAlmostEqual(deduction.amount, 961.0, places=2)
        self.assertAlmostEqual(deduction.difference, -39.0, places=2)
        deduction.validate_expenses()

        moves = deduction.voucher_ids | deduction.move_id
        moves |= self.env["account.move"].search([("expenses_deduction_id", "=", deduction.id)])
        partners = {
            self.employee_partner.id: "employee",
            self.supplier.id: "supplier",
        }
        accounts = {
            self.acc_cash.id: "cash",
            self.acc_542.id: "542",
            self.acc_exp.id: "6xx",
            self.acc_payable.id: "401",
        }
        journals = {
            self.cash_journal.id: "cash",
            self.adv_journal.id: "adv",
            self.diary_journal.id: "diem",
        }

        def journal_key(journal):
            return journals.get(journal.id) or journal.type

        result = sorted(
            (
                str(aml.date),
                journal_key(aml.journal_id),
                accounts.get(aml.account_id.id, aml.account_id.code),
                partners.get(aml.partner_id.id, aml.partner_id.name or ""),
                round(aml.debit, 2),
                round(aml.credit, 2),
            )
            for aml in moves.line_ids
        )
        # Referința: aceleași valori obținute rulând scenariul pe 19.0. Taxa de test nu are cont
        # de TVA în repartiție, deci TVA-ul ajunge pe contul de cheltuială (6xx).
        expected = sorted(
            [
                # avans: Dr 542 = Cr casă
                ("2026-01-15", "cash", "542", "employee", 1000.0, 0.0),
                ("2026-01-15", "cash", "cash", "employee", 0.0, 1000.0),
                # diferența de restituit (961 - 1000): Dr casă = Cr 542 (pe data avansului)
                ("2026-01-15", "cash", "cash", "employee", 39.0, 0.0),
                ("2026-01-15", "cash", "542", "employee", 0.0, 39.0),
                # chitanțe: Cazare 500 + TVA 105 (pe deasupra), Masă 100 + TVA 21 (inclus)
                ("2026-01-18", "purchase", "6xx", "supplier", 500.0, 0.0),
                ("2026-01-18", "purchase", "6xx", "supplier", 105.0, 0.0),
                ("2026-01-18", "purchase", "401", "supplier", 0.0, 605.0),
                ("2026-01-18", "purchase", "6xx", "supplier", 100.0, 0.0),
                ("2026-01-18", "purchase", "6xx", "supplier", 21.0, 0.0),
                ("2026-01-18", "purchase", "401", "supplier", 0.0, 121.0),
                # decontare din avans: Dr 401 (furnizor) = Cr 542 (angajat), per chitanță și plată directă
                ("2026-01-18", "adv", "401", "supplier", 605.0, 0.0),
                ("2026-01-18", "adv", "542", "employee", 0.0, 605.0),
                ("2026-01-18", "adv", "401", "supplier", 121.0, 0.0),
                ("2026-01-18", "adv", "542", "employee", 0.0, 121.0),
                ("2026-01-18", "adv", "401", "supplier", 150.0, 0.0),
                ("2026-01-18", "adv", "542", "employee", 0.0, 150.0),
                # diurnă: Dr 625 = Cr 542
                ("2026-01-20", "diem", "6xx", "employee", 85.0, 0.0),
                ("2026-01-20", "diem", "542", "employee", 0.0, 85.0),
            ]
        )
        self.maxDiff = None
        self.assertEqual(result, expected)
        # 542 închis pe angajat, chitanțele și factura deschisă stinse din avans
        lines_542 = moves.line_ids.filtered(lambda aml: aml.account_id == self.acc_542)
        self.assertAlmostEqual(sum(lines_542.mapped("balance")), 0.0, places=2)
        self.assertTrue(all(v.payment_state in ("paid", "in_payment") for v in deduction.voucher_ids))
        self.assertTrue(bill.payment_state in ("paid", "in_payment"))

    def test_report_renders(self):
        """Raportul de decont se randează (QWeb server-side, fără t-esc ignorat)."""
        deduction = self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": self.employee.id,
                "advance": 100.0,
                "days": 1,
                "travel_order": "OD-1",
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
                "journal_diem_id": self.diary_journal.id,
                "account_diem_id": self.acc_exp.id,
            }
        )
        self.env["deltatech.expenses.deduction.line"].create(
            {
                "expenses_deduction_id": deduction.id,
                "name": "Cazare",
                "amount": 100.0,
                "partner_id": self.supplier.id,
                "expense_account_id": self.acc_exp.id,
            }
        )
        html, _report_type = self.env["ir.actions.report"]._render_qweb_html(
            "deltatech_expenses.action_report_deltatech_expenses_deduction", deduction.ids
        )
        html = html.decode() if isinstance(html, bytes) else str(html)
        self.assertIn("Decont cheltuieli", html)
        # 2 documente (linia + diurna) → ramura cu numărul afișat prin t-out
        self.assertIn("acte justificative specificate", html)
        self.assertIn("OD-1", html)

    def _new_deduction(self, advance, **vals):
        values = {
            "date_advance": fields.Date.today(),
            "employee_id": self.employee.id,
            "advance": advance,
            "journal_id": self.cash_journal.id,
            "expense_journal_id": self.adv_journal.id,
            "journal_diem_id": self.diary_journal.id,
            "account_diem_id": self.acc_exp.id,
        }
        values.update(vals)
        deduction = self.env["deltatech.expenses.deduction"].create(values)
        deduction.validate_advance()
        return deduction

    def _new_line(self, deduction, amount, taxes=None, **vals):
        values = {
            "expenses_deduction_id": deduction.id,
            "name": "Cheltuială",
            "amount": amount,
            "tax_ids": [(6, 0, (taxes or self.env["account.tax"]).ids)],
            "expense_account_id": self.acc_exp.id,
            "partner_id": self.supplier.id,
        }
        values.update(vals)
        return self.env["deltatech.expenses.deduction.line"].create(values)

    def _foreign_currency(self, company):
        """An active currency different from the company currency, with a rate far from 1."""
        currency = (
            self.env["res.currency"]
            .with_context(active_test=False)
            .search([("id", "!=", company.currency_id.id), ("name", "in", ["EUR", "USD", "CHF"])], limit=1)
        )
        currency.active = True
        self.env["res.currency.rate"].create(
            {"currency_id": currency.id, "rate": 0.2, "name": fields.Date.today(), "company_id": company.id}
        )
        return currency

    def test_line_currency_is_company_currency(self):
        """EXPENSES-002: a currency sent with the line is ignored, the line is in the company currency
        of the deduction, so totals and posting add only amounts in the same currency."""
        foreign = self._foreign_currency(self.company)
        deduction = self._new_deduction(200.0)
        # tax included: the receipt total (121) is the line amount, whatever the tax computation of the line
        line = self._new_line(deduction, 121.0, self.tax_incl_21, currency_id=foreign.id)
        self.assertEqual(line.currency_id, self.company.currency_id)
        self.assertEqual(deduction.currency_id, self.company.currency_id)
        line.write({"currency_id": foreign.id})
        self.assertEqual(line.currency_id, self.company.currency_id)
        self.assertAlmostEqual(deduction.amount_vouchers, 121.0, places=2)
        deduction.validate_expenses()
        voucher = deduction.voucher_ids
        self.assertEqual(voucher.currency_id, self.company.currency_id)
        self.assertAlmostEqual(voucher.amount_total, 121.0, places=2)
        lines_542 = self._lines_for_expenses(deduction).filtered(lambda l: l.account_id == self.acc_542)
        self.assertAlmostEqual(sum(lines_542.mapped("debit")), sum(lines_542.mapped("credit")), places=2)

    def test_line_currency_follows_deduction_company(self):
        """EXPENSES-002: the line currency comes from the deduction company, not from the main company
        of the user (who works in another allowed company)."""
        foreign = self._foreign_currency(self.company)
        company_b = self.env["res.company"].create({"name": "Expenses company B", "currency_id": foreign.id})
        self.env.user.company_ids |= company_b
        self.assertEqual(self.env.user.company_id, self.company)
        env_b = self.env(context=dict(self.env.context, allowed_company_ids=[company_b.id, self.company.id]))
        account_b = env_b["account.account"].create(
            {"name": "Cash B", "code": "5311B", "account_type": "asset_cash", "company_ids": [(6, 0, company_b.ids)]}
        )
        journal_b = env_b["account.journal"].create(
            {
                "name": "Cash B",
                "code": "CSHB",
                "type": "general",
                "company_id": company_b.id,
                "default_account_id": account_b.id,
            }
        )
        deduction = env_b["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": self.employee.id,
                "company_id": company_b.id,
                "journal_id": journal_b.id,
                "account_diem_id": account_b.id,
            }
        )
        line = env_b["deltatech.expenses.deduction.line"].create(
            {"expenses_deduction_id": deduction.id, "name": "Taxi", "amount": 50.0, "expense_account_id": account_b.id}
        )
        self.assertEqual(deduction.currency_id, foreign)
        self.assertEqual(line.currency_id, foreign)
        self.assertAlmostEqual(deduction.amount_vouchers, 50.0, places=2)
