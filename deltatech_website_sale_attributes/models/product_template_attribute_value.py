# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


from odoo import fields, models

class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    def _only_active(self):
        res = super()._only_active()
        if self.env.context.get('website_id'):
            res = res.filtered(lambda ptav: ptav.product_attribute_value_id.visibility == 'visible')
        return res
