# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    purchase_source_currency_id = fields.Many2one(
        "res.currency",
        string="Order Currency",
        compute="_compute_purchase_source_currency_id",
        help="Currency of the purchase orders billed here, when it is a single one and differs from the bill currency.",
    )
    purchase_vendor_rate = fields.Float(
        string="Vendor Rate",
        digits=(12, 6),
        copy=False,
        help="Exchange rate stated on the vendor invoice: bill currency for 1 unit of the order "
        "currency (e.g. 5.1 RON for 1 EUR). When set, the order prices are converted at this "
        "rate instead of the Odoo rate of the bill date.",
    )

    @api.depends("currency_id", "invoice_line_ids.purchase_line_id.currency_id")
    def _compute_purchase_source_currency_id(self):
        for move in self:
            currencies = move.invoice_line_ids.purchase_line_id.currency_id
            if move.is_purchase_document() and len(currencies) == 1 and currencies != move.currency_id:
                move.purchase_source_currency_id = currencies
            else:
                move.purchase_source_currency_id = False

    @api.constrains("purchase_vendor_rate")
    def _check_purchase_vendor_rate(self):
        for move in self:
            if move.purchase_vendor_rate < 0:
                raise ValidationError(self.env._("The vendor rate cannot be negative."))

    def _get_purchase_vendor_rate(self, order_currency):
        """Vendor rate to apply to order lines in ``order_currency``, or None."""
        self.ensure_one()
        if self.purchase_vendor_rate > 0 and order_currency and order_currency != self.currency_id:
            currencies = self.invoice_line_ids.purchase_line_id.currency_id
            if not currencies or currencies == order_currency:
                return self.purchase_vendor_rate
        return None

    def _purchase_currency_reset_prices(self, only_other_currency):
        date = self.invoice_date or self.date or fields.Date.context_today(self)
        for line in self.invoice_line_ids:
            po_line = line.purchase_line_id
            if line.display_type != "product" or not po_line:
                continue
            if only_other_currency and po_line.currency_id == self.currency_id:
                continue
            line.price_unit = po_line._get_invoice_price_unit(
                self.currency_id,
                date,
                line.product_uom_id,
                rate=self._get_purchase_vendor_rate(po_line.currency_id),
            )

    @api.onchange("invoice_date")
    def _onchange_invoice_date_purchase_currency(self):
        if self.is_purchase_document():
            self._purchase_currency_reset_prices(only_other_currency=True)

    @api.onchange("currency_id")
    def _onchange_currency_purchase_currency(self):
        if self.is_purchase_document():
            self._purchase_currency_reset_prices(only_other_currency=False)

    @api.onchange("purchase_vendor_rate")
    def _onchange_purchase_vendor_rate(self):
        if self.is_purchase_document():
            self._purchase_currency_reset_prices(only_other_currency=True)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("currency_id", "move_id.invoice_date", "move_id.purchase_vendor_rate")
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
            po_price = po_line._get_invoice_price_unit(
                line.currency_id,
                date,
                line.product_uom_id,
                rate=move._get_purchase_vendor_rate(po_line.currency_id),
            )
            po_price_discounted = po_price * (1 - po_line.discount / 100)
            price = line.price_unit * (1 - line.discount / 100)
            price_msg = ""
            if price_compare := line.currency_id.compare_amounts(po_price_discounted, price):
                price_msg = f" {'⬇' if price_compare > 0 else '⬆'} {line.currency_id.format(po_price_discounted)}"
            line.purchase_matching_issue_msg = (price_msg + qty_msg) or False
        return res
