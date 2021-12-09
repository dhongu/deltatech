# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ServiceAgreement(models.Model):
    _inherit = "service.agreement"

    total_costs = fields.Float(string="Total Cost", readonly=True)  # se va calcula din suma avizelor
    total_percent = fields.Float(string="Total percent", readonly=True)  # se va calcula (consum/factura)*100
