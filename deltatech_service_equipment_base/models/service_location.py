# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models


class ServiceLocation(models.Model):
    _name = "service.location"
    _description = "Service Location"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Reference", index=True, default=lambda self: _("New"))
    display_name = fields.Char(compute="_compute_display_name")
    partner_id = fields.Many2one("res.partner", string="Customer")
    contact_id = fields.Many2one(
        "res.partner",
        string="Contact Person",
        tracking=True,
        domain=[("type", "=", "contact"), ("is_company", "=", False)],
    )
    technician_user_id = fields.Many2one("res.users", string="Responsible", tracking=True)
    note = fields.Text(string="Notes")
    parent_id = fields.Many2one("service.location", string="Functional Location")
    children_ids = fields.One2many("service.location", "parent_id", string="Children")
    address_id = fields.Many2one("res.partner", string="Address")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New") or vals.get("name") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code("service.location") or _("New")
        return super().create(vals_list)
