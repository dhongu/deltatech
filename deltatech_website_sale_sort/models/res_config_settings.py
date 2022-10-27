# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    product_price_pricelist = fields.Many2one(
        "product.pricelist",
        "Pricelist for product price compute",
        config_parameter="sale.product_price_pricelist",
        help="Pricelist from which product prices are computed",
    )
    price_from_pricelist_taxes = fields.Boolean(
        "Compute price with taxes",
        config_parameter="sale.price_from_pricelist_taxes",
        help="If checked, taxes are added to the product price",
    )
