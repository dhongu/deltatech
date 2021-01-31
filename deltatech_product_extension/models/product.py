# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models

import odoo.addons.decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = "product.template"

    dimensions = fields.Char(string="Dimensions")
    shelf_life = fields.Float(string="Shelf Life", digits=dp.get_precision("Product Unit of Measure"))
    uom_shelf_life = fields.Many2one(
        "uom.uom", string="Unit of Measure Shelf Life", help="Unit of Measure for Shelf Life", group_operator="avg"
    )

    manufacturer = fields.Many2one("res.partner", string="Manufacturer", domain=[("is_manufacturer", "=", True)])
