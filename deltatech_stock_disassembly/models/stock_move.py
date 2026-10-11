# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    disassembly_id = fields.Many2one("stock.disassembly", string="Disassembly Report", index="btree_not_null")
    disassembly_line_id = fields.Many2one("stock.disassembly.line", index="btree_not_null")

    def _compute_reference(self):
        with_report = self.filtered("disassembly_id")
        for move in with_report:
            move.reference = move.disassembly_id.name
        return super(StockMove, self - with_report)._compute_reference()

    def _create_account_move(self):
        # the disassembly report posts one entry for all its moves, with the accounts of its own
        return super(StockMove, self.filtered(lambda move: not move.disassembly_id))._create_account_move()

    def _get_value_from_production(self, quantity, at_date=None):
        line = self.disassembly_line_id
        if not line or line.line_type != "product":
            return super()._get_value_from_production(quantity, at_date=at_date)
        line_qty = line._get_product_qty()
        value = line.value * quantity / line_qty if line_qty else 0.0
        return {
            "value": value,
            "quantity": quantity,
            "description": self.env._(
                "%(value)s for %(quantity)s %(unit)s from %(report)s",
                value=self.company_currency_id.format(value),
                quantity=quantity,
                unit=self.product_id.uom_id.name,
                report=line.disassembly_id.display_name,
            ),
        }
