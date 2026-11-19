# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, format_date, formatLang


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
        help="Exchange rate used for the order prices: bill currency for 1 unit of the order "
        "currency (e.g. 5.1 RON for 1 EUR). Filled in with the Odoo rate of the bill date; type "
        "the rate stated on the vendor invoice after setting the bill date.",
    )
    purchase_odoo_rate = fields.Float(
        string="Odoo Rate",
        digits=(12, 6),
        copy=False,
        help="Last rate filled in automatically in Vendor Rate; a different Vendor Rate was typed by hand.",
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

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves.filtered(lambda m: m.state == "draft" and not m.purchase_vendor_rate):
            if move.purchase_source_currency_id:
                move._purchase_vendor_rate_refresh()
                move._purchase_currency_reset_prices(only_other_currency=True)
        return moves

    def _get_purchase_currency_date(self):
        return self.invoice_date or self.date or fields.Date.context_today(self)

    def _get_purchase_odoo_rate(self):
        """Odoo rate of the bill date: bill currency for 1 unit of the order currency."""
        self.ensure_one()
        source = self.purchase_source_currency_id
        if not source:
            return 0.0
        return source._get_conversion_rate(
            source, self.currency_id, self.company_id, self._get_purchase_currency_date()
        )

    def _purchase_vendor_rate_refresh(self):
        """Put the Odoo rate of the bill date in Vendor Rate.

        Returns the rate typed by hand that was replaced, or None.
        """
        self.ensure_one()
        typed = None
        if (
            self.purchase_vendor_rate
            and self.purchase_odoo_rate
            and float_compare(self.purchase_vendor_rate, self.purchase_odoo_rate, precision_digits=6)
        ):
            typed = self.purchase_vendor_rate
        rate = self._get_purchase_odoo_rate()
        self.purchase_vendor_rate = rate
        self.purchase_odoo_rate = rate
        return typed

    def _get_purchase_vendor_rate(self, order_currency):
        """Vendor rate to apply to order lines in ``order_currency``, or None."""
        self.ensure_one()
        if self.purchase_vendor_rate > 0 and order_currency and order_currency != self.currency_id:
            currencies = self.invoice_line_ids.purchase_line_id.currency_id
            if not currencies or currencies == order_currency:
                return self.purchase_vendor_rate
        return None

    def _purchase_currency_reset_prices(self, only_other_currency):
        date = self._get_purchase_currency_date()
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
        if not self.is_purchase_document():
            return None
        typed = None
        if self.purchase_source_currency_id:
            typed = self._purchase_vendor_rate_refresh()
        self._purchase_currency_reset_prices(only_other_currency=True)
        if typed:
            return {
                "warning": {
                    "title": self.env._("Vendor rate replaced"),
                    "message": self.env._(
                        "The vendor rate %(typed)s was replaced with the rate of %(date)s: %(rate)s "
                        "%(currency)s for 1 %(order_currency)s. If the vendor invoice states another rate, "
                        "type it again.",
                        typed=formatLang(self.env, typed, digits=4),
                        date=format_date(self.env, self._get_purchase_currency_date()),
                        rate=formatLang(self.env, self.purchase_vendor_rate, digits=4),
                        currency=self.currency_id.name,
                        order_currency=self.purchase_source_currency_id.name,
                    ),
                }
            }
        return None

    @api.onchange("currency_id")
    def _onchange_currency_purchase_currency(self):
        if self.is_purchase_document():
            self._purchase_vendor_rate_refresh()
            self._purchase_currency_reset_prices(only_other_currency=False)

    @api.onchange("purchase_vendor_rate")
    def _onchange_purchase_vendor_rate(self):
        if not self.is_purchase_document():
            return
        if not self.purchase_vendor_rate and self.purchase_source_currency_id:
            self._purchase_vendor_rate_refresh()
        self._purchase_currency_reset_prices(only_other_currency=True)

    @api.onchange("purchase_vendor_bill_id", "purchase_id")
    def _onchange_purchase_auto_complete(self):
        res = super()._onchange_purchase_auto_complete()
        if self.purchase_source_currency_id and not self.purchase_vendor_rate:
            self._purchase_vendor_rate_refresh()
            self._purchase_currency_reset_prices(only_other_currency=True)
        return res
