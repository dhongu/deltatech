# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    display_type = fields.Selection(selection_add=[("texture", "Texture")], ondelete={"texture": "set default"})


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    texture = fields.Image(string="Texture")
