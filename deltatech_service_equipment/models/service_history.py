# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ServiceHistory(models.Model):
    _name = "service.history"
    _description = "ServiceHistory"

    name = fields.Char()
    date = fields.Date(required=True, index=True, default=fields.Date.context_today)
    agreement_id = fields.Many2one("service.agreement", string="Service Agreement", ondelete="cascade")
    equipment_id = fields.Many2one("service.equipment", string="Equipment", ondelete="cascade")
    description = fields.Char()
