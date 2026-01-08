# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    partner_id = fields.Many2one("res.partner", domain=[("parent_id", "=", False)])
