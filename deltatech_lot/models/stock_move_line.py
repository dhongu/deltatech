# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _default_lot_name(self):
        picking_type_code = self.env.context.get("picking_type_code", False)
        if picking_type_code and picking_type_code == "incoming":
            product = self.env["product.product"].browse(self.env.context.get("default_product_id", False))
            if product.tracking == "lot":
                return self.env["ir.sequence"].next_by_code("stock.lot.serial")
        return False

    @api.onchange("location_id", "lot_id")
    def onchange_location_id(self):
        domain = [("product_id", "=", self.product_id.id), ("company_id", "=", self.company_id.id)]
        if self.location_id and self.product_id.tracking != "none":
            quant_domain = [("product_id", "=", self.product_id.id), ("location_id", "=", self.location_id.id)]
            quants = self.env["stock.quant"].search(quant_domain)
            domain += [("quant_ids", "in", quants.ids)]

        return {"domain": {"lot_id": domain}}
