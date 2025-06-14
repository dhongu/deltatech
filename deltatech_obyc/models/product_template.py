# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    valuation_class_id = fields.Many2one(
        "product.valuation.class",
        string="Valuation Class",
        company_dependent=True,
    )
