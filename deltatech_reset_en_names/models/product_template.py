# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def button_reset_en_names(self):
        """Reset the name and description of the product to the English version"""
        for product in self:
            original_name = product.name
            en_name = product.with_context(lang="en_US").name
            if original_name != en_name:
                product.with_context(lang="en_US").write({"name": original_name})
