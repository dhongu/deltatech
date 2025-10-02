# © 2025 Deltatech
# See README.rst file on the addons root folder for license details


from odoo import fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    restrict_incomplete_delivery = fields.Boolean(string="Restrict Incomplete Delivery", default=False)
