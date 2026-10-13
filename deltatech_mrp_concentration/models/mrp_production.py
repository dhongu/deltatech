# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class MrpProduction(models.Model):
    """Manufacturing Orders"""

    _inherit = "mrp.production"

    concentration = fields.Float(string="Concentration", help="Concentration of the final product")
    concentration_primary = fields.Float(string="Concentration Primary", help="Concentration of the main ingredient")
    bom_id = fields.Many2one("mrp.bom")

    @api.onchange("bom_id")
    def _onchange_bom_id(self):
        if self.bom_id.concentration:
            self.concentration = self.bom_id.concentration
        if self.bom_id.concentration_primary:
            self.concentration_primary = self.bom_id.concentration_primary

    @api.onchange("concentration_primary", "concentration", "product_qty")
    def _onchange_concentration_primary(self):
        if not self.concentration_primary:
            return
        primary_bom_line = self.bom_id.bom_line_ids.filtered(lambda x: x.ingredient_type == "primary")
        if primary_bom_line:
            move_line = self.move_raw_ids.filtered(lambda x: x.bom_line_id == primary_bom_line)
            # cantitatea de baza * concentatia produsului finit / concentratia ingredientului principal
            product_uom_qty = self.product_qty * self.concentration / self.concentration_primary
            move_line.product_uom_qty = product_uom_qty

            # dilution adds the secondary ingredient, concentration produces a by-product:
            # the group not used by the current ratio is set to zero
            diff = self.product_qty - product_uom_qty
            secondary_bom_line = self.bom_id.bom_line_ids.filtered(lambda x: x.ingredient_type == "secondary")
            if secondary_bom_line:
                move_line = self.move_raw_ids.filtered(lambda x: x.bom_line_id in secondary_bom_line)
                move_line.product_uom_qty = max(diff, 0.0)
            # product_qty is computed on stock moves and cannot be written, the demand is product_uom_qty
            self.move_byproduct_ids.product_uom_qty = max(-diff, 0.0)
