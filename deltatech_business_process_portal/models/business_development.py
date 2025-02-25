# ©  2023 Deltatech
# ©  2025 NextERP Romania
# See README.rst file on addons root folder for license details

from odoo import models


class BusinessDevelopment(models.Model):
    _name = "business.development"
    _inherit = ["portal.mixin", "business.development"]
