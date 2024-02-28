# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ObjectHistory(models.Model):
    """
    Parallel document history
    """

    _name = "object.history"
    _description = "Object history"
    _inherit = ["mail.thread"]
    _order = "id desc"

    active = fields.Boolean(default=True)
    name = fields.Char("Name", required=True)
    object_name = fields.Char(string="Parent name")
    partner_id = fields.Many2one("res.partner", string="Related partner")
    description = fields.Html("Description")
    res_model = fields.Char(
        "Resource Model", readonly=True, index=True, help="The database model this history will be attached to."
    )
    res_id = fields.Many2oneReference(
        "Resource ID", model_field="res_model", readonly=True, index=True, help="The record id this is attached to."
    )
    company_id = fields.Many2one(
        "res.company", string="Company", index=True, change_default=True, default=lambda self: self.env.company
    )

    def action_open_document(self):
        """Opens the related record based on the model and ID"""
        self.ensure_one()
        return {
            "res_id": self.res_id,
            "res_model": self.res_model,
            "target": "current",
            "type": "ir.actions.act_window",
            "view_mode": "form",
        }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        if (
            "res_model" in res
            and res["res_model"]
            and "res_id" in res
            and res["res_id"]
            and (
                res["res_model"] == "res.partner"
                or res["res_model"] == "account.move"
                or res["res_model"] == "stock.picking"
            )
        ):
            parent = self.env[res["res_model"]].browse(res["res_id"])
            if res["res_model"] == "res.partner":
                partner = self.env["res.partner"].browse(res["res_id"])
                res["partner_id"] = partner.id
            res["object_name"] = parent.name

        return res
