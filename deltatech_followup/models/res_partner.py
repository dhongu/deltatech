# ©  2015-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    send_followup = fields.Boolean("Send followup e-mails")
