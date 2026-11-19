# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _purchase_currency_reset_prices(self, only_other_currency):
        date = self.invoice_date or self.date or fields.Date.context_today(self)
        for line in self.invoice_line_ids:
            po_line = line.purchase_line_id
            if line.display_type != "product" or not po_line:
                continue
            if only_other_currency and po_line.currency_id == self.currency_id:
                continue
            line.price_unit = po_line._get_invoice_price_unit(self.currency_id, date, line.product_uom_id)

    @api.onchange("invoice_date")
    def _onchange_invoice_date_purchase_currency(self):
        if self.is_purchase_document():
            self._purchase_currency_reset_prices(only_other_currency=True)

    @api.onchange("currency_id")
    def _onchange_currency_purchase_currency(self):
        if self.is_purchase_document():
            self._purchase_currency_reset_prices(only_other_currency=False)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("currency_id", "move_id.invoice_date")
    def _compute_purchase_matching_issue_msg(self):
        res = super()._compute_purchase_matching_issue_msg()
        # the standard flag compares the bill price with the order price as numbers; when the
        # bill is in another currency, compare with the order price converted to it
        for line in self:
            po_line = line.purchase_line_id
            if not line.product_id or not po_line or po_line.currency_id == line.currency_id:
                continue
            msg = line.purchase_matching_issue_msg or ""
            qty_msg = msg[msg.index(" ⚠") :] if " ⚠" in msg else ""
            move = line.move_id
            date = move.invoice_date or move.date or fields.Date.context_today(line)
            po_price = po_line._get_invoice_price_unit(line.currency_id, date, line.product_uom_id)
            po_price_discounted = po_price * (1 - po_line.discount / 100)
            price = line.price_unit * (1 - line.discount / 100)
            price_msg = ""
            if price_compare := line.currency_id.compare_amounts(po_price_discounted, price):
                price_msg = f" {'⬇' if price_compare > 0 else '⬆'} {line.currency_id.format(po_price_discounted)}"
            line.purchase_matching_issue_msg = (price_msg + qty_msg) or False
        return res
