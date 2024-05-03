# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HistoryAddRecord(models.TransientModel):
    _name = "history.add.wizard"
    _description = "Add history record wizard"

    name = fields.Char(string="Name")
    description = fields.Html(string="Description")
    res_model = fields.Char("Resource Model", readonly=False)
    res_id = fields.Many2oneReference("Resource ID", model_field="res_model", readonly=False)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        change_default=True,
        default=lambda self: self.env.company,
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        active_model = self.env.context.get("active_model", False)
        if active_id and active_model:
            defaults["res_id"] = active_id
            defaults["res_model"] = active_model
        else:
            raise UserError(_("Object not found"))
        return defaults

    def add_history(self):
        if self.res_id and self.res_model:
            values = {
                "active": True,
                "name": self.name,
                "description": self.description,
                "res_model": self.res_model,
                "res_id": self.res_id,
            }
            res = self.env["object.history"].create(values)
            return res
        return False
