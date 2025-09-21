# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessArea(models.Model):
    _name = "business.area"
    _description = "Business Area"

    name = fields.Char(string="Name", required=True)
    process_group_ids = fields.One2many(
        string="Business process groups",
        comodel_name="business.process.group",
        inverse_name="area_id",
    )
    responsible_id = fields.Many2one(
        string="Responsible",
        domain="[('is_company', '=', False)]",
        comodel_name="res.partner",
    )


class BusinessProcessGroup(models.Model):
    _name = "business.process.group"
    _description = "Business Process Group"

    name = fields.Char(string="Name", required=True)
    area_id = fields.Many2one(string="Business area", comodel_name="business.area")
