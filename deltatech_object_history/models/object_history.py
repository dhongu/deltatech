# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


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
    description = fields.Html("Description")
    res_model = fields.Char(
        "Resource Model",
        readonly=True,
        index=True,
        help="The database model this history will be attached to.",
    )
    res_id = fields.Many2oneReference(
        "Resource ID",
        model_field="res_model",
        readonly=True,
        index=True,
        help="The record id this is attached to.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        change_default=True,
        default=lambda self: self.env.company,
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
