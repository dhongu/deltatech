# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    qty_available = fields.Float("Quantity Available", digits="Product Unit of Measure")
