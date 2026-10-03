# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    concentration = fields.Float(string="Concentration", help="Concentration of the final product")
    concentration_primary = fields.Float(string="Concentration Primary", help="Concentration of the main ingredient")

    @api.onchange("concentration_primary", "concentration", "product_qty")
    def _onchange_concentration_primary(self):
        if not self.concentration_primary:
            return
        primary_bom_line = self.bom_line_ids.filtered(lambda x: x.ingredient_type == "primary")
        if primary_bom_line:
            # cantitatea de baza * concentatia produsului finit / concentratia ingredientului principal
            primary_bom_line.product_qty = self.product_qty * self.concentration / self.concentration_primary

            diff = self.product_qty - primary_bom_line.product_qty
            if diff > 0:
                secondary_bom_line = self.bom_line_ids.filtered(lambda x: x.ingredient_type == "secondary")
                if secondary_bom_line:
                    secondary_bom_line.product_qty = self.product_qty - primary_bom_line.product_qty
            else:
                secondary_bom_line = self.byproduct_ids
                if secondary_bom_line:
                    secondary_bom_line.product_qty = -1 * diff


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    ingredient_type = fields.Selection(
        [("primary", "Primary"), ("secondary", "Secondary"), ("normal", "Normal")],
        string="Ingredient Type",
        default="normal",
    )
