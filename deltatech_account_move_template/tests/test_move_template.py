# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestMoveTemplate(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.company_data["default_journal_misc"]
        cls.Template = cls.env["account.move.template"]

    @classmethod
    def _account(cls, prefix):
        return cls.env["account.account"].search(
            [
                *cls.env["account.account"]._check_company_domain(cls.env.company),
                ("code", "=like", f"{prefix}%"),
            ],
            order="code",
            limit=1,
        )

    def _template(self, lines, name="Test template"):
        return self.Template.create(
            {
                "name": name,
                "journal_id": self.journal.id,
                "line_ids": [Command.create(vals) for vals in lines],
            }
        )

    def _run(self, template, amounts=None, **vals):
        with Form(self.env["account.move.template.run"].with_context(default_template_id=template.id)) as wizard:
            for key, value in vals.items():
                setattr(wizard, key, value)
            for index in range(len(wizard.line_ids)):
                with wizard.line_ids.edit(index) as line:
                    if amounts and line.code in amounts:
                        line.amount = amounts[line.code]
        return wizard.save()._create_move()

    def _payroll_template(self):
        return self._template(
            [
                {"code": "GROSS", "account_id": self._account("641").id, "direction": "debit"},
                {
                    "code": "CAS",
                    "account_id": self._account("4315").id,
                    "direction": "credit",
                    "amount_type": "percent",
                    "percent": 25,
                    "base_code": "GROSS",
                },
                {
                    "code": "CASS",
                    "account_id": self._account("4316").id,
                    "direction": "credit",
                    "amount_type": "formula",
                    "formula": "round(GROSS * 0.10)",
                },
                {"code": "TAX", "account_id": self._account("444").id, "direction": "credit"},
                {"code": "NET", "account_id": self._account("421").id, "direction": "credit", "amount_type": "balance"},
            ],
            name="Payroll",
        )

    def test_payroll_entry(self):
        template = self._payroll_template()
        move = self._run(template, {"GROSS": 5000.0, "TAX": 326.0})
        self.assertEqual(move.move_template_id, template)
        self.assertEqual(move.state, "draft")
        self.assertRecordValues(
            move.line_ids.sorted(lambda line: (-line.debit, line.credit)),
            [
                {"account_id": self._account("641").id, "debit": 5000.0, "credit": 0.0},
                {"account_id": self._account("444").id, "debit": 0.0, "credit": 326.0},
                {"account_id": self._account("4316").id, "debit": 0.0, "credit": 500.0},
                {"account_id": self._account("4315").id, "debit": 0.0, "credit": 1250.0},
                {"account_id": self._account("421").id, "debit": 0.0, "credit": 2924.0},
            ],
        )
        self.assertEqual(template.move_count, 1)

    def test_codes_filled_and_formula_order(self):
        # the formula line comes before the line it uses: the order is given by the dependencies
        template = self._template(
            [
                {
                    "account_id": self._account("4426").id,
                    "direction": "debit",
                    "amount_type": "formula",
                    "formula": "L2 * 0.21",
                },
                {"account_id": self._account("612").id, "direction": "debit"},
                {"account_id": self._account("401").id, "direction": "credit", "amount_type": "balance"},
            ]
        )
        self.assertEqual(template.line_ids.mapped("code"), ["L1", "L2", "L3"])
        move = self._run(template, {"L2": 1000.0}, partner_id=self.partner_a)
        self.assertRecordValues(
            move.line_ids.sorted("balance"),
            [
                {"account_id": self._account("401").id, "balance": -1210.0, "partner_id": self.partner_a.id},
                {"account_id": self._account("4426").id, "balance": 210.0, "partner_id": self.partner_a.id},
                {"account_id": self._account("612").id, "balance": 1000.0, "partner_id": self.partner_a.id},
            ],
        )

    def test_tax_lines_and_balance(self):
        tax = self.company_data["default_tax_purchase"]
        template = self._template(
            [
                {"code": "BASE", "account_id": self._account("612").id, "direction": "debit", "tax_ids": [tax.id]},
                {"code": "SUP", "account_id": self._account("401").id, "direction": "credit", "amount_type": "balance"},
            ]
        )
        move = self._run(template, {"BASE": 1000.0}, partner_id=self.partner_a)
        tax_line = move.line_ids.filtered("tax_line_id")
        self.assertEqual(tax_line.tax_line_id, tax)
        self.assertTrue(tax_line.tax_tag_ids or not tax.invoice_repartition_line_ids.tag_ids)
        supplier_line = move.line_ids.filtered(lambda line: line.account_id == self._account("401"))
        self.assertAlmostEqual(supplier_line.credit, 1000.0 + tax_line.debit)
        self.assertEqual(len(move.line_ids), 3)
        self.assertEqual(supplier_line.partner_id, self.partner_a)

    def test_negative_amount_switches_side(self):
        template = self._template(
            [
                {"code": "A", "account_id": self._account("612").id, "direction": "debit"},
                {"code": "B", "account_id": self._account("401").id, "direction": "credit", "amount_type": "balance"},
            ]
        )
        move = self._run(template, {"A": -100.0}, partner_id=self.partner_a)
        self.assertRecordValues(
            move.line_ids.sorted("balance"),
            [
                {"account_id": self._account("612").id, "balance": -100.0},
                {"account_id": self._account("401").id, "balance": 100.0},
            ],
        )

    def test_fixed_amount_and_post(self):
        template = self._template(
            [
                {
                    "code": "A",
                    "account_id": self._account("612").id,
                    "direction": "debit",
                    "amount_type": "fixed",
                    "fixed_amount": 300,
                },
                {
                    "code": "B",
                    "account_id": self._account("401").id,
                    "direction": "credit",
                    "amount_type": "fixed",
                    "fixed_amount": 300,
                },
            ]
        )
        move = self._run(template, partner_id=self.partner_a, post=True)
        self.assertEqual(move.state, "posted")
        self.assertEqual(move.amount_total, 300.0)

    def test_unbalanced_without_balance_line(self):
        template = self._template(
            [
                {"code": "A", "account_id": self._account("612").id, "direction": "debit"},
                {"code": "B", "account_id": self._account("401").id, "direction": "credit"},
            ]
        )
        with self.assertRaises(UserError):
            self._run(template, {"A": 100.0, "B": 90.0}, partner_id=self.partner_a)

    def test_all_zero(self):
        with self.assertRaises(UserError):
            self._run(self._payroll_template())

    def test_invalid_templates(self):
        account = self._account("612").id
        cases = [
            # unknown code
            [{"code": "A", "account_id": account, "amount_type": "formula", "formula": "X * 2"}],
            # loop
            [
                {"code": "A", "account_id": account, "amount_type": "formula", "formula": "B + 1"},
                {"code": "B", "account_id": account, "amount_type": "formula", "formula": "A + 1"},
            ],
            # duplicate code
            [{"code": "A", "account_id": account}, {"code": "A", "account_id": account}],
            # two balance lines
            [
                {"code": "A", "account_id": account, "amount_type": "balance"},
                {"code": "B", "account_id": account, "amount_type": "balance"},
            ],
            # a line using the balance line
            [
                {"code": "A", "account_id": account, "amount_type": "balance"},
                {"code": "B", "account_id": account, "amount_type": "percent", "percent": 10, "base_code": "A"},
            ],
            # invalid code and syntax
            [{"code": "1A", "account_id": account}],
            [{"code": "A", "account_id": account, "amount_type": "formula", "formula": "2 *"}],
        ]
        for index, lines in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(ValidationError), self.cr.savepoint():
                self._template(lines, name=f"Invalid {index}")

    def test_copy(self):
        template = self._payroll_template()
        copy = template.copy()
        self.assertEqual(copy.name, "Payroll (copy)")
        self.assertEqual(copy.line_ids.mapped("code"), template.line_ids.mapped("code"))

    def test_default_formula_and_parameters(self):
        template = self._template(
            [
                {"code": "TOTAL", "direction": "debit"},
                {"code": "RATE", "direction": "debit", "fixed_amount": 21},
                {
                    "code": "VAT",
                    "account_id": self._account("4426").id,
                    "direction": "debit",
                    "formula": "TOTAL * RATE / (100 + RATE)",
                },
                {
                    "code": "NDUE",
                    "account_id": self._account("44282").id,
                    "direction": "credit",
                    "amount_type": "balance",
                },
            ]
        )
        wizard = Form(self.env["account.move.template.run"].with_context(default_template_id=template.id))
        with wizard.line_ids.edit(0) as line:
            self.assertEqual(line.code, "TOTAL")
            line.amount = 1210.0
        with wizard.line_ids.edit(2) as line:
            self.assertTrue(line.use_default)
            self.assertEqual(line.amount, 210.0)
        with wizard.line_ids.edit(1) as line:
            line.amount = 19.0
        with wizard.line_ids.edit(2) as line:
            self.assertEqual(line.amount, 193.19)
        move = wizard.save()._create_move()
        # the parameters are not recorded
        self.assertEqual(len(move.line_ids), 2)
        self.assertEqual(move.amount_total, 193.19)
        # an amount typed over the suggestion wins
        wizard = Form(self.env["account.move.template.run"].with_context(default_template_id=template.id))
        with wizard.line_ids.edit(2) as line:
            line.use_default = False
            line.amount = 50.0
        self.assertEqual(wizard.save()._create_move().amount_total, 50.0)

    def test_ro_templates(self):
        self.Template.action_load_ro_templates()
        templates = self.Template.search([("company_id", "=", self.env.company.id)])
        self.assertEqual(len(templates), 10)
        # loading again creates nothing
        created, skipped = self.Template._load_ro_templates(self.env.company)
        self.assertFalse(created)
        self.assertEqual(len(skipped), 10)

        payroll = templates.filtered(lambda t: t.line_ids.filtered(lambda line: line.code == "CAM"))
        move = self._run(payroll, {"GROSS": 10000.0, "TAX": 585.0, "ADV": 1000.0})
        balances = {}
        for line in move.line_ids:
            balances[line.account_id.code[:3]] = balances.get(line.account_id.code[:3], 0) + line.balance
        self.assertEqual(
            balances,
            {
                "641": 10000.0,
                "421": -10000.0 + 2500.0 + 1000.0 + 585.0 + 1000.0,
                "431": -3500.0,
                "444": -585.0,
                "425": -1000.0,
                "646": 225.0,
                "436": -225.0,
            },
        )

        loan = templates.filtered(
            lambda t: t.line_ids.filtered(lambda line: (line.account_id.code or "").startswith("8031"))
        )
        receipt = loan.filtered(
            lambda t: t.line_ids.filtered(lambda line: line.code == "VALUE" and line.direction == "debit")
        )
        move = self._run(receipt, {"VALUE": 50000.0}, post=True)
        self.assertEqual(move.state, "posted")
        self.assertEqual(set(move.line_ids.account_id.mapped("account_type")), {"off_balance"})

        rent = templates.filtered(
            lambda t: t.line_ids.filtered(lambda line: (line.account_id.code or "").startswith("4081"))
        )
        move = self._run(rent, {"RENT": 1000.0, "RATE": 21.0}, partner_id=self.partner_a)
        self.assertEqual(move.amount_total, 1210.0)
