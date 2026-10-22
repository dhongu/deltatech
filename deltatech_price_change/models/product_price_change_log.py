# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.tools import float_compare


class ProductPriceChangeLog(models.Model):
    _name = "product.price.change.log"
    _description = "Product List Price Change Log"
    _order = "date desc, id desc"
    _rec_name = "product_tmpl_id"

    product_tmpl_id = fields.Many2one(
        "product.template", "Product", required=True, index=True, ondelete="cascade", readonly=True
    )
    date = fields.Date(required=True, index=True, readonly=True, default=fields.Date.context_today)
    old_price = fields.Float("Old Sale Price", digits="Product Price", readonly=True)
    new_price = fields.Float("New Sale Price", digits="Product Price", readonly=True)
    user_id = fields.Many2one("res.users", "Changed by", readonly=True, default=lambda self: self.env.user)
    company_id = fields.Many2one("res.company", index=True, readonly=True)
    line_ids = fields.One2many("product.price.change.line", "log_id", readonly=True)
    price_change_id = fields.Many2one(
        "product.price.change",
        "Price Change Document",
        compute="_compute_price_change_id",
        store=True,
        index=True,
    )

    @api.depends("line_ids.price_change_id")
    def _compute_price_change_id(self):
        for log in self:
            log.price_change_id = log.line_ids.price_change_id[:1]

    @api.model
    def _log_list_price_change(self, templates, old_prices):
        """Keep one log per product and day: the old price is the price before the first change of the day,
        the new price is the current one. A log already in a confirmed document is not touched any more."""
        digits = self.env["decimal.precision"].precision_get("Product Price")
        today = fields.Date.context_today(self)
        Log = self.sudo()
        for template in templates:
            old_price = old_prices.get(template.id)
            new_price = template.list_price
            if old_price is None or not float_compare(old_price, new_price, precision_digits=digits):
                continue
            log = Log.search(
                [
                    ("product_tmpl_id", "=", template.id),
                    ("date", "=", today),
                    "|",
                    ("price_change_id", "=", False),
                    ("price_change_id.state", "=", "draft"),
                ],
                limit=1,
            )
            if log:
                if not float_compare(log.old_price, new_price, precision_digits=digits):
                    # back at the price of the previous day: there is no change left
                    log.unlink()
                else:
                    log.write({"new_price": new_price})
                    log.line_ids.write({"new_price": new_price})
            else:
                Log.create(
                    {
                        "product_tmpl_id": template.id,
                        "date": today,
                        "old_price": old_price,
                        "new_price": new_price,
                        "company_id": template.company_id.id or self.env.company.id,
                    }
                )
