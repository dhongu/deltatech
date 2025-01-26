# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons rcoot folder for license details

from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestStockValuation(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.account = cls.env["account.account"].create(
            {
                "name": "Account A",
                "code": "1234",
                "user_type_id": cls.env.ref("account.data_account_type_current_assets").id,
                "stock_valuation": True,
            }
        )

        cls.sale_journal = cls.env["account.journal"].create(
            {
                "name": "Test Journal",
                "type": "sale",
                "code": "TEST",
            }
        )

        cls.env.company.set_stock_valuation_at_company_level()
        config = cls.env["res.config.settings"].create(
            {
                "valuation_area_level": "company",
                "valuation_area_id": cls.env.company.valuation_area_id.id,
            }
        )
        config.refresh_stock_valuation()

    def test_account_move(self):
        today = fields.Date.today()
        today = fields.Date.from_string(today)
        date = today + relativedelta(day=1, months=-1, days=15)

        invoices = self.env["account.move"].create(
            [
                {
                    "move_type": "out_invoice",
                    "invoice_date": date,
                    "date": date,
                    "partner_id": self.partner_a.id,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "product_id": self.product_a.id,
                                "account_id": self.account.id,
                                "quantity": 5.0,
                                "price_unit": 1000.0,
                                "tax_ids": [Command.set(self.company_data["default_tax_sale"].ids)],
                            }
                        )
                    ],
                },
                {
                    "move_type": "out_invoice",
                    "invoice_date": date,
                    "date": date,
                    "partner_id": self.company_data["company"].partner_id.id,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "product_id": self.product_a.id,
                                "account_id": self.account.id,
                                "quantity": 2.0,
                                "price_unit": 1500.0,
                                "tax_ids": [Command.set(self.company_data["default_tax_sale"].ids)],
                            }
                        )
                    ],
                },
                {
                    "move_type": "out_refund",
                    "invoice_date": date,
                    "date": date,
                    "partner_id": self.partner_a.id,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "product_id": self.product_a.id,
                                "account_id": self.account.id,
                                "quantity": 3.0,
                                "price_unit": 1000.0,
                                "tax_ids": [Command.set(self.company_data["default_tax_sale"].ids)],
                            }
                        )
                    ],
                },
                {
                    "move_type": "in_invoice",
                    "invoice_date": date,
                    "date": date,
                    "partner_id": self.partner_b.id,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "product_id": self.product_b.id,
                                "account_id": self.account.id,
                                "quantity": 10.0,
                                "price_unit": 800.0,
                                "tax_ids": [Command.set(self.company_data["default_tax_purchase"].ids)],
                            }
                        )
                    ],
                },
            ]
        )
        invoices.action_post()
