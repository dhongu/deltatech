# ©  2015-2021 Terrabit Solutions
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import fields, models


class CommonHistory(models.Model):
    _name = "common.history"
    _description = "Service Equipment History"

    name = fields.Char()
    date = fields.Date(required=True, index=True, default=fields.Date.context_today)
    agreement_id = fields.Many2one("service.agreement", string="Service Agreement", ondelete="cascade")
    equipment_id = fields.Many2one("service.equipment", string="Equipment", ondelete="cascade")
    description = fields.Char()
