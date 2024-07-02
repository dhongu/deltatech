# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    pallet_product_id = fields.Many2one("product.product")
    pallet_qty_min = fields.Float(digits="Product Unit of Measure")  # cantitatea minima pe palet
    pallet_price = fields.Float(
        "Pallet Price",
        default=1.0,
        digits="Product Price",
        compute="_compute_pallet_price",
    )

    def _compute_pallet_price(self):
        # todo: de verificat cum se determina lista de preturi principala
        main_pricelist = self.env['product.pricelist'].search([('company_id', '=', self.env.company.id)], limit=1)
        for template in self:
            price = main_pricelist._get_product_price(template, template.pallet_qty_min)
            template.pallet_price = price
