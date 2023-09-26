# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ServiceChangeInvoiceDate(models.TransientModel):
    _name = "service.change.invoice.date"
    _description = "Service change invoice date"

    date_invoice = fields.Date(string="Invoice Date")

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_ids = self.env.context.get("active_ids", False)
        if active_ids:
            cons = self.env["service.consumption"].browse(active_ids[0])
            defaults["date_invoice"] = cons.date_invoice
        return defaults

    def do_change(self):
        active_ids = self.env.context.get("active_ids", False)

        domain = [("invoice_id", "=", False), ("id", "in", active_ids)]

        consumptions = self.env["service.consumption"].search(domain)

        if not consumptions:
            raise UserError(_("There were no service consumption !"))

        consumptions.write({"date_invoice": self.date_invoice})

        return {
            "domain": "[('id','in', [" + ",".join(map(str, [rec.id for rec in consumptions])) + "])]",
            "name": _("Service Consumption"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "service.consumption",
            "view_id": False,
            "type": "ir.actions.act_window",
        }
