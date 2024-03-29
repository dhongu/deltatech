# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    equi_type_required = fields.Boolean(string="Equipment type required")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    equi_type_required = fields.Boolean(related="categ_id.equi_type_required")
    equi_type_id = fields.Many2one("service.equipment.type", string="Equipment type")
