# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _default_lot_name(self):
        picking_type_code = self.env.context.get("picking_type_code", False)
        if picking_type_code and picking_type_code == "incoming":
            product = self.env["product.product"].browse(self.env.context.get("default_product_id", False))
            if product.tracking == "lot":
                return self.env["ir.sequence"].next_by_code("stock.lot.serial")
        return False

    lot_name = fields.Char(default=_default_lot_name)
