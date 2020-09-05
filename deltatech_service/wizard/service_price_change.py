# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import except_orm


class ServicePriceChange(models.TransientModel):
    _name = "service.price.change"
    _description = "Service price change"

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    product_id = fields.Many2one("product.product", string="Product", required=True, domain=[("type", "=", "service")])

    price_unit = fields.Float(string="Unit Price", required=True, digits="Service Price")

    currency_id = fields.Many2one("res.currency", string="Currency", required=True, default=_default_currency)
    reference = fields.Char("Reference")

    @api.model
    def default_get(self, fields_list):
        defaults = super(ServicePriceChange, self).default_get(fields_list)
        active_ids = self.env.context.get("active_ids", False)
        if active_ids:
            cons = self.env["service.consumption"].browse(active_ids[0])
            defaults["product_id"] = cons.product_id.id
            defaults["price_unit"] = cons.price_unit
            defaults["currency_id"] = cons.currency_id.id
            defaults["reference"] = cons.name
        return defaults

    @api.onchange("product_id")
    def onchange_scanned_ean(self):
        price_unit = self.product_id.list_price
        self.price_unit = self.env.user.company_id.currency_id.compute(price_unit, self.currency_id)

    def do_price_change(self):
        active_ids = self.env.context.get("active_ids", False)

        if active_ids:
            domain = [("invoice_id", "=", False), ("product_id", "=", self.product_id.id), ("id", "in", active_ids)]
        else:
            domain = [("invoice_id", "=", False), ("product_id", "=", self.product_id.id)]

        consumptions = self.env["service.consumption"].search(domain)

        if not consumptions:
            raise except_orm(_("No consumptions!"), _("There were no service consumption !"))

        consumptions.write({"price_unit": self.price_unit, "currency_id": self.currency_id.id, "name": self.reference})

        price_unit = self.currency_id.compute(self.price_unit, self.env.user.company_id.currency_id)

        self.product_id.write({"list_price": price_unit})

        return {
            "domain": "[('id','in', [" + ",".join(map(str, [rec.id for rec in consumptions])) + "])]",
            "name": _("Service Consumption"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "service.consumption",
            "view_id": False,
            "type": "ir.actions.act_window",
        }
