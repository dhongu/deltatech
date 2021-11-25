# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    equipment_id = fields.Many2one("service.equipment", string="Equipment", store=True)
    agreement_id = fields.Many2one(
        "service.agreement", string="Service Agreement", related="equipment_id.agreement_id", store=True, readonly=False
    )
