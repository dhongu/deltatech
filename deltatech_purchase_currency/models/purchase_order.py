# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    journal_id = fields.Many2one(
        "account.journal",
        string="Invoicing Journal",
        domain=[("type", "=", "purchase")],
        check_company=True,
        copy=True,
        help="If set, the vendor bill is created in this journal and in its currency "
        "(the company currency when the journal has none); the order prices are converted "
        "at the bill date rate. If empty, the bill is in the order currency.",
    )

    def _get_invoice_currency(self):
        """Currency of the vendor bill created from this order."""
        self.ensure_one()
        if self.journal_id:
            return self.journal_id.currency_id or self.company_id.currency_id
        return self.currency_id

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.journal_id:
            invoice_vals["journal_id"] = self.journal_id.id
            invoice_vals["currency_id"] = self._get_invoice_currency().id
        return invoice_vals


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _get_invoice_price_unit(self, to_currency, date, uom=None, rate=None):
        """Unit price of this order line expressed in ``to_currency`` and ``uom``.

        Single place where the order price is converted for the vendor bill: override it to
        apply another rate (e.g. the BNR rate plus a percentage). ``rate`` is the vendor rate
        typed on the bill (``to_currency`` for 1 unit of the order currency); when given, it
        must win over any computed rate.
        """
        self.ensure_one()
        price_unit = self.price_unit
        if uom and self.product_uom_id and uom != self.product_uom_id:
            price_unit = self.product_uom_id._compute_price(price_unit, uom)
        if to_currency and self.currency_id and to_currency != self.currency_id:
            if rate:
                price_unit = price_unit * rate
            else:
                price_unit = self.currency_id._convert(price_unit, to_currency, self.company_id, date, round=False)
        return price_unit

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move=move)
        if res.get("display_type") == "product":
            rate = None
            if move:
                to_currency = move.currency_id
                date = move.invoice_date or move.date
                rate = move._get_purchase_vendor_rate(self.currency_id)
            else:
                to_currency = self.order_id._get_invoice_currency()
                date = False
            date = date or fields.Date.context_today(self)
            if to_currency != self.currency_id:
                res["price_unit"] = self._get_invoice_price_unit(to_currency, date, rate=rate)
        return res
