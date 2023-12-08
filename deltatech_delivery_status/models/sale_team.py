# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    postpone_payment_transfer = fields.Boolean(string="Postpone delivery for transfer payment")
