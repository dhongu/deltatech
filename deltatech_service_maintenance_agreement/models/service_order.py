# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ServiceOrder(models.Model):
    _inherit = "service.order"

    emplacement = fields.Char(string="Emplacement", readonly=True)
    agreement_id = fields.Many2one("service.agreement", string="Service Agreement", readonly=True)
