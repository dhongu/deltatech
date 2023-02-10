# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_email = fields.Char("Partner e-mail", related="partner_id.email", readonly=True)
    partner_phone = fields.Char("Partner phone", related="partner_id.phone", readonly=True)
    partner_mobile = fields.Char("Partner mobile", related="partner_id.mobile", readonly=True)
