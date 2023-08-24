# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessDevelopment(models.Model):
    _name = "business.development"
    _description = "Business Development"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Text(string="Description")
    area_id = fields.Many2one(string="Business area", comodel_name="business.area", required=True)
    type_id = fields.Many2one(string="Type", comodel_name="business.development.type", required=True)

    approved = fields.Selection(
        [("draft", "Draft"), ("approved", "Approved"), ("rejected", "Rejected"), ("pending", "Pending")],
        string="Approved",
        default="draft",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("specification", "Specification"),
            ("development", "Development"),
            ("test", "Test"),
            ("production", "Production"),
        ],
        string="State",
        default="draft",
    )
