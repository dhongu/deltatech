# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(
        selection_add=[("last_purchase_price", "Last Purchase Price")],
        ondelete={"last_purchase_price": "set default"},
    )
