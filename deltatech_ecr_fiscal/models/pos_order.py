# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models


class PosOrder(models.Model):
    _name = "pos.order"
    _inherit = ["pos.order", "deltatech.ecr.fiscal.mixin"]
