# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    purchase_update_product_price = fields.Boolean(
        "Update product price", config_parameter="purchase.update_product_price"
    )
    purchase_update_list_price = fields.Boolean("Update list price", config_parameter="purchase.update_list_price")
    purchase_update_standard_price = fields.Boolean(
        "Update standard price", config_parameter="purchase.update_standard_price"
    )
    purchase_add_supplier_to_product = fields.Boolean(
        "Add supplier to product",
        default=True,
        config_parameter="purchase.add_supplier_to_product",
    )
    purchase_force_price_at_validation = fields.Boolean(
        "Force supplier price at PO and bill confirmation",
        default=False,
        config_parameter="purchase.force_price_at_validation",
        help="Force product supplier price at purchase order validation and supplier bill validation",
    )
