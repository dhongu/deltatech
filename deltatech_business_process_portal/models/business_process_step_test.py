# ©  2023 Deltatech
# ©  2025 NextERP Romania
# See README.rst file on addons root folder for license details

from odoo import models


class BusinessProcessStepTest(models.Model):
    _name = "business.process.step.test"
    _inherit = ["portal.mixin", "business.process.step.test"]
