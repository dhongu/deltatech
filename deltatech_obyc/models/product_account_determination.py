# © 2025 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


TRANSACTION_KEYS = [
    # transcation  for stock valuation
    ('stock_valuation', 'Stock Valuation'),  # In SAP is BSX


    # Purchase transactions
    ('stock_receipt', 'Stock Receipt'),     # in SAP is WRX
    ('return_to_supplier', 'Return to Supplier'),

    # Sale transactions
    ('stock_delivery', 'Stock Delivery'),
    ('return_from_customer', 'Return from Customer'),
    ('stock_income', 'Income'),

    # Dropshipping transactions
    ('dropship', 'Dropshipping'),
    ('dropship_return', 'Dropshipping Return'),

    # Internal transfers
    ('internal_transfer', 'Internal Transfer'),
    ('internal_transfer_out', 'Internal Transfer Out'),
    ('internal_transfer_in', 'Internal Transfer In'),

    # Inventory adjustments
    ('inventory_adjustment_plus', 'Inventory Adjustment Plus'),
    ('inventory_adjustment_minus', 'Inventory Adjustment Minus'),

    # Production transactions
    ('production_issue', 'Production Issue'),
    ('production_receipt', 'Production Receipt'),

]

class ProductAccountDetermination(models.Model):
    _name = "product.account.determination"
    _description = "Product Account Determination"

    transaction_key = fields.Selection(
        selection=TRANSACTION_KEYS, string="Transaction Key", required=True,
    )
    account_modifier_id = fields.Many2one("account.modifier", string="Account Modifier")
    valuation_class_id = fields.Many2one("product.valuation.class", string="Valuation Class")
    valuation_area_id = fields.Many2one("valuation.area", string="Valuation Area")
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)

    acc_src_id = fields.Many2one("account.account", string="Source Account")
    acc_dest_id = fields.Many2one("account.account", string="Destination Account")
    acc_valuation_id = fields.Many2one("account.account", string="Valuation Account")

    def _compute_display_name(self):
        for item in self:
            item.display_name = (
                f"{item.transaction_key} - {item.valuation_class_id.name}"
                f" - {item.valuation_area_id.name} "
                f"- {item.account_modifier_id.name if item.account_modifier_id else 'None'}"
            )

    def _get_rule_account(self, valuation_area, valuation_class, transaction_key, account_modifier, company):
        modifier_name = account_modifier.name if account_modifier else "None"
        valuation_class_name = valuation_class.name
        company_name = company.name
        area_name = valuation_area.name
        transaction_key_name = dict(self._fields["transaction_key"].selection).get(transaction_key)

        message = (
            f"Determining accounts for transaction key '{transaction_key_name}', "
            f"account modifier '{modifier_name}', valuation class '{valuation_class_name}', "
            f"valuation area '{area_name}' and company '{company_name}'."
        )
        _logger.info(message)

        rule = self.env["product.account.determination"].search(
            [
                ("transaction_key", "=", transaction_key),
                ("account_modifier_id", "=", account_modifier.id),
                ("valuation_class_id", "=", valuation_class.id),
                ("valuation_area_id", "=", valuation_area.id),
                ("company_id", "=", company.id),
            ],
            limit=1,
        )

        if not rule:
            raise UserError(
                _(
                    f"No account determination rule found for transaction key '{transaction_key_name}', "
                    f"account modifier '{modifier_name}', valuation class '{valuation_class_name}', "
                    f"valuation area '{area_name}' and company '{company_name}'."
                )
            )

        return rule
