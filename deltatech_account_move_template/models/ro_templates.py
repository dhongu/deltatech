# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import Command, models


class AccountMoveTemplate(models.Model):
    _inherit = "account.move.template"

    def _ro_template_definitions(self):
        """Optional templates for the Romanian chart of accounts.

        Accounts are given by code prefix and looked up in the company chart.
        """

        def line(code, account, direction, amount_type="input", **vals):
            return {"code": code, "account": account, "direction": direction, "amount_type": amount_type, **vals}

        def parameter(code, name, **vals):
            return {"code": code, "account": False, "direction": "debit", "name": name, **vals}

        vat_rate = parameter("RATE", self.env._("VAT rate (%)"))
        return [
            {
                "name": self.env._("Monthly rent - invoice not received (tenant)"),
                "note": self.env._(
                    "Records the rent of the month when the invoice comes later. Real estate rent is VAT exempt: "
                    "leave the VAT rate 0. If the lessor opted for taxation, and for the rent of movable goods "
                    "(equipment, cars), enter the rate 21. When the invoice arrives: 408 = 401 and 4426 = 4428."
                ),
                "lines": [
                    line("RENT", "612", "debit", name=self.env._("Rent")),
                    vat_rate,
                    line(
                        "VAT",
                        "44282",
                        "debit",
                        "formula",
                        formula="RENT * RATE / 100",
                        name=self.env._("VAT not yet due"),
                    ),
                    line("SUP", "4081", "credit", "balance", name=self.env._("Invoices not received")),
                ],
            },
            {
                "name": self.env._("Monthly rent - invoice to be issued (lessor)"),
                "note": self.env._(
                    "Records the rent income of the month when the invoice is issued later. Real estate rent is "
                    "VAT exempt: leave the VAT rate 0. If you opted for taxation, and for the rent of movable "
                    "goods (equipment, cars), enter the rate 21. When the invoice is issued: 4111 = 418 and "
                    "4427 = 4428."
                ),
                "lines": [
                    line("RENT", "706", "credit", name=self.env._("Rent")),
                    vat_rate,
                    line(
                        "VAT",
                        "44281",
                        "credit",
                        "formula",
                        formula="RENT * RATE / 100",
                        name=self.env._("VAT not yet due"),
                    ),
                    line("CUS", "418", "debit", "balance", name=self.env._("Invoices to be issued")),
                ],
            },
            {
                "name": self.env._("Depreciation - tangible assets"),
                "note": self.env._(
                    "Monthly depreciation recorded by hand. Change account 2813 to the one of the asset group "
                    "(2812 buildings, 2814 other tangible assets). Do not use it for assets managed with the "
                    "Assets module: the depreciation would be recorded twice."
                ),
                "lines": [
                    line("DEP", "6811", "debit", name=self.env._("Depreciation")),
                    line("ACC", "2813", "credit", "balance", name=self.env._("Accumulated depreciation")),
                ],
            },
            {
                "name": self.env._("Depreciation - intangible assets"),
                "note": self.env._(
                    "Monthly amortisation recorded by hand. Account 2808 is for software and other intangible "
                    "assets; use 2805 for concessions, patents, licences and trademarks, and 2803 for development "
                    "costs. Do not use it for assets managed with the Assets module: the amortisation would be "
                    "recorded twice."
                ),
                "lines": [
                    line("DEP", "6811", "debit", name=self.env._("Amortisation")),
                    line("ACC", "2808", "credit", "balance", name=self.env._("Accumulated amortisation")),
                ],
            },
            {
                "name": self.env._("Asset received for use (loan for use or rent) - receipt"),
                "note": self.env._(
                    "Off-balance record of an asset received under a loan for use or a rent contract, at the "
                    "value in the handover report. Off-balance accounts are kept in single entry: account 8000 is "
                    "only the technical counterpart that Odoo needs to balance the entry. Use 8033 for goods "
                    "in custody and 8039 for goods in consignment."
                ),
                "lines": [
                    line("VALUE", "8031", "debit", name=self.env._("Asset received for use")),
                    line("TECH", "8000", "credit", "balance", name=self.env._("Off-balance counterpart")),
                ],
            },
            {
                "name": self.env._("Asset received for use (loan for use or rent) - return"),
                "note": self.env._(
                    "Off-balance record of the return of an asset received for use, at the receipt value."
                ),
                "lines": [
                    line("VALUE", "8031", "credit", name=self.env._("Asset returned")),
                    line("TECH", "8000", "debit", "balance", name=self.env._("Off-balance counterpart")),
                ],
            },
            {
                "name": self.env._("Payroll - external payslip"),
                "note": self.env._(
                    "Records the payslip computed in another program. Enter the totals of the payslip: the "
                    "contributions are suggested from the gross amount (25%, 10%, 2.25%), but the payslip "
                    "totals prevail (part-time work, rounding per employee). Sick leave is not included."
                ),
                "lines": [
                    line("GROSS", "641", "debit", name=self.env._("Gross salaries")),
                    line("PAY", "421", "credit", "formula", formula="GROSS", name=self.env._("Salaries payable")),
                    line(
                        "CAS", "4315", "credit", formula="GROSS * 0.25", name=self.env._("Social security contribution")
                    ),
                    line(
                        "CASS",
                        "4316",
                        "credit",
                        formula="GROSS * 0.10",
                        name=self.env._("Health insurance contribution"),
                    ),
                    line("TAX", "444", "credit", name=self.env._("Income tax")),
                    line("ADV", "425", "credit", name=self.env._("Salary advances")),
                    line("GARN", "427", "credit", name=self.env._("Garnishments")),
                    line(
                        "WITHHELD",
                        "421",
                        "debit",
                        "formula",
                        formula="CAS + CASS + TAX + ADV + GARN",
                        name=self.env._("Withholdings from salaries"),
                    ),
                    line(
                        "CAM", "646", "debit", formula="GROSS * 0.0225", name=self.env._("Work insurance contribution")
                    ),
                    line(
                        "CAMP",
                        "436",
                        "credit",
                        "formula",
                        formula="CAM",
                        name=self.env._("Work insurance contribution"),
                    ),
                ],
            },
            {
                "name": self.env._("Meal vouchers granted"),
                "note": self.env._("The purchase of the vouchers is recorded separately (5328 = 401)."),
                "lines": [
                    line("VOUCH", "6422", "debit", name=self.env._("Meal vouchers")),
                    line("STOCK", "5328", "credit", "balance", name=self.env._("Other values")),
                ],
            },
            {
                "name": self.env._("VAT on cash basis - due on collection"),
                "note": self.env._(
                    "Makes the VAT due for an amount collected. Use it only for opening balances or corrections: "
                    "the cash basis taxes of Odoo already do it on reconciliation. Invoices with chargeable event "
                    "before 1 August 2025 use the rates of that time (19%, 9%, 5%)."
                ),
                "lines": [
                    parameter("TOTAL", self.env._("Amount collected, VAT included")),
                    parameter("RATE", self.env._("VAT rate (%)"), fixed_amount=21),
                    line(
                        "VAT",
                        "44281",
                        "debit",
                        "formula",
                        formula="TOTAL * RATE / (100 + RATE)",
                        name=self.env._("VAT not yet due"),
                    ),
                    line("DUE", "4427", "credit", "balance", name=self.env._("Output VAT")),
                ],
            },
            {
                "name": self.env._("VAT on cash basis - deductible on payment"),
                "note": self.env._(
                    "Makes the VAT deductible for an amount paid. Use it only for opening balances or "
                    "corrections: the cash basis taxes of Odoo already do it on reconciliation. Invoices with "
                    "chargeable event before 1 August 2025 use the rates of that time (19%, 9%, 5%)."
                ),
                "lines": [
                    parameter("TOTAL", self.env._("Amount paid, VAT included")),
                    parameter("RATE", self.env._("VAT rate (%)"), fixed_amount=21),
                    line(
                        "VAT",
                        "4426",
                        "debit",
                        "formula",
                        formula="TOTAL * RATE / (100 + RATE)",
                        name=self.env._("Input VAT"),
                    ),
                    line("NDUE", "44282", "credit", "balance", name=self.env._("VAT not yet due")),
                ],
            },
        ]

    def _get_ro_technical_account(self, company):
        """Off-balance counterpart account 8000, created when missing."""
        Account = self.env["account.account"].with_company(company)
        account = Account.search(
            [*Account._check_company_domain(company), ("code", "=like", "8000%")], order="code", limit=1
        )
        if not account:
            account = Account.create(
                {
                    "code": "800000",
                    "name": self.env._("Off-balance technical counterpart"),
                    "account_type": "off_balance",
                    "company_ids": [Command.link(company.id)],
                }
            )
        return account

    def _load_ro_templates(self, company):
        Account = self.env["account.account"].with_company(company)
        journal = self.with_company(company)._default_journal()
        created = self.browse()
        skipped = []
        for definition in self._ro_template_definitions():
            name = definition["name"]
            if self.with_context(active_test=False).search_count(
                [("company_id", "=", company.id), ("name", "=", name)], limit=1
            ):
                skipped.append(name)
                continue
            line_commands = []
            for line in definition["lines"]:
                vals = dict(line)
                prefix = vals.pop("account")
                if prefix == "8000":
                    account = self._get_ro_technical_account(company)
                elif prefix:
                    account = Account.search(
                        [*Account._check_company_domain(company), ("code", "=like", f"{prefix}%")],
                        order="code",
                        limit=1,
                    )
                    if not account:
                        break
                else:
                    account = Account
                vals["account_id"] = account.id
                line_commands.append(Command.create(vals))
            else:
                created |= self.create(
                    {
                        "name": name,
                        "company_id": company.id,
                        "journal_id": journal.id,
                        "ref": definition.get("ref"),
                        "note": definition.get("note"),
                        "line_ids": line_commands,
                    }
                )
                continue
            skipped.append(name)
        return created, skipped
