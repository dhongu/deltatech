# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ServiceDistribution(models.TransientModel):
    _name = "service.distribution"
    _description = "Service distribution"

    product_id = fields.Many2one("product.product", string="Product", required=True, domain=[("type", "=", "service")])
    quantity = fields.Float(string="Quantity", required=True, digits="Product Unit of Measure")
    amount = fields.Float(string="Amount", required=True)
    type = fields.Selection([("qty", "Quantity"), ("val", "Value")], default="qty", string="Distribution type")
    mode = fields.Selection([("divide", "Divide"), ("fix", "Fix")], string="Mode", required=True, default="fix")
    reference = fields.Char("Reference")
    add_values = fields.Boolean("Add to existing?", default=True)

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_ids = self.env.context.get("active_ids", False)
        if active_ids:
            defaults["amount"] = 0
            consumptions = self.env["service.consumption"].browse(active_ids)
            for consumption in consumptions:
                defaults["product_id"] = consumption.product_id.id
                defaults["quantity"] = consumption.quantity
                defaults["reference"] = consumption.name
                defaults["amount"] += consumption.quantity * consumption.price_unit
        return defaults

    def do_distribution(self):
        active_ids = self.env.context.get("active_ids", False)

        if active_ids:
            domain = [("invoice_id", "=", False), ("product_id", "=", self.product_id.id), ("id", "in", active_ids)]
        else:
            domain = [("invoice_id", "=", False), ("product_id", "=", self.product_id.id)]

        consumptions = self.env["service.consumption"].search(domain)

        if not consumptions:
            raise UserError(_("There were no service consumption !"))

        if self.type == "qty":
            if self.mode == "divide":
                qty = self.quantity / len(consumptions)
            else:
                qty = self.quantity
            consumptions.write({"quantity": qty, "name": self.reference})
        else:
            price_unit = self.amount / len(consumptions)
            if self.add_values:
                for cons in consumptions:
                    crt_value = cons.price_unit + price_unit
                    if self.reference:
                        name = cons.name + self.reference
                    else:
                        name = cons.name
                    cons.write({"quantity": 1, "price_unit": crt_value, "name": name})
            else:
                consumptions.write({"quantity": 1, "price_unit": price_unit, "name": self.reference})

        return {
            "domain": "[('id','in', [" + ",".join(map(str, [rec.id for rec in consumptions])) + "])]",
            "name": _("Service Consumption"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "service.consumption",
            "view_id": False,
            "type": "ir.actions.act_window",
        }
