# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSupplierPayment(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        super().setUpClass()
        company = cls.company_data["company"]
        cls.env.user.company_id = company

        def account(code):
            return cls.env["account.account"].search(
                [("code", "=like", f"{code}%"), ("company_ids", "in", company.id)], limit=1
            )

        cls.acc_542 = account("542")
        cls.acc_4092 = account("4092")
        cls.cash_journal = cls.env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", company.id)], limit=1
        )
        # jurnal de avansuri de trezorerie (542), de tip casa ca sa aiba metode de plata
        cls.adv_journal = cls.env["account.journal"].create(
            {
                "name": "Avansuri trezorerie",
                "code": "AVT",
                "type": "cash",
                "default_account_id": cls.acc_542.id,
                "company_id": company.id,
            }
        )
        cls.employee = cls.env["res.partner"].create({"name": "Angajat X"})
        cls.supplier = cls.env["res.partner"].create({"name": "Furnizor Y", "is_company": True})

    def _old_bill(self, amount):
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.supplier.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [(0, 0, {"name": "Factura veche", "price_unit": amount, "tax_ids": []})],
            }
        )
        bill.action_post()
        return bill

    def _expenses(self, amount):
        expenses = self.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "date_expense": fields.Date.today(),
                "employee_id": self.employee.id,
                "advance": 1000.0,
                "journal_id": self.cash_journal.id,
                "expense_journal_id": self.adv_journal.id,
            }
        )
        expenses.validate_advance()
        self.env["deltatech.expenses.deduction.line"].create(
            {
                "expenses_deduction_id": expenses.id,
                "name": "Plata factura veche",
                "type": "supplier_payment",
                "partner_id": self.supplier.id,
                "amount": amount,
            }
        )
        return expenses

    def test_supplier_payment_partial(self):
        bill = self._old_bill(500.0)
        expenses = self._expenses(300.0)
        expenses.validate_expenses()

        self.assertEqual(expenses.state, "done")
        self.assertAlmostEqual(bill.amount_residual, 200.0)
        self.assertEqual(bill.payment_state, "partial")
        payment_line = expenses.payment_ids.move_id.line_ids.filtered(
            lambda aml: aml.account_id.account_type == "liability_payable"
        )
        self.assertTrue(payment_line.reconciled)
        # plata: Dr 401 furnizor = Cr 542
        credit_542 = expenses.payment_ids.move_id.line_ids.filtered(lambda aml: aml.account_id == self.acc_542)
        self.assertAlmostEqual(credit_542.credit, 300.0)
        self.assertAlmostEqual(payment_line.debit, 300.0)

    def test_receipt_and_supplier_payment(self):
        bill = self._old_bill(500.0)
        expenses = self._expenses(500.0)
        self.env["deltatech.expenses.deduction.line"].create(
            {
                "expenses_deduction_id": expenses.id,
                "name": "Bon fiscal",
                "type": "expenses",
                "partner_id": self.supplier.id,
                "amount": 100.0,
            }
        )
        expenses.validate_expenses()

        self.assertIn(bill.payment_state, ("paid", "in_payment"))
        self.assertTrue(expenses.voucher_ids)
        self.assertIn(expenses.voucher_ids.payment_state, ("paid", "in_payment"))
        # avans 1000, cheltuieli 600: diferenta de 400 se intoarce in casa, 542 se inchide
        lines = self.env["account.move.line"].search([("move_id.expenses_deduction_id", "=", expenses.id)])
        lines |= expenses.payment_ids.move_id.line_ids
        lines_542 = lines.filtered(lambda aml: aml.account_id == self.acc_542)
        self.assertAlmostEqual(sum(lines_542.mapped("balance")), 0.0)

    def test_supplier_payment_over_bill_goes_to_4092(self):
        bill = self._old_bill(500.0)
        expenses = self._expenses(700.0)
        expenses.validate_expenses()

        self.assertIn(bill.payment_state, ("paid", "in_payment"))
        lines_4092 = self.env["account.move.line"].search(
            [("move_id.expenses_deduction_id", "=", expenses.id), ("account_id", "=", self.acc_4092.id)]
        )
        self.assertAlmostEqual(sum(lines_4092.mapped("debit")), 200.0)
        self.assertEqual(lines_4092.partner_id, self.supplier)

        expenses.invalidate_expenses()
        self.assertEqual(expenses.state, "draft")
        self.assertAlmostEqual(bill.amount_residual, 500.0)
        self.assertFalse(lines_4092.exists())
