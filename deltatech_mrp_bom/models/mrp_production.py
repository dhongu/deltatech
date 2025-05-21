# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.onchange('product_id')
    def _change_product_id(self):
        for production in self:
            domain = [("product_tmpl_id", "=", production.product_tmpl_id.id),('base_type', '=', 'base')]
            base_bom = self.env["mrp.bom"].search(domain, limit=1)
            if base_bom and production.product_id:
                domain = [("product_id", "=", production.product_id.id),('base_type', '=', 'derived')]
                derived_bom = self.env["mrp.bom"].search(domain, limit=1)
                if not derived_bom:
                    derived_bom = self.env["mrp.bom"].create({
                        "product_tmpl_id": production.product_tmpl_id.id,
                        "product_id": production.product_id.id,
                        "base_type": 'derived',
                    })
                derived_bom.recompute_from_base()
                production.bom_id = derived_bom

    def action_confirm(self):
        for production in self:
            if production.bom_id.base_type == 'derived':
                production.bom_id.recompute_from_base()

        return super().action_confirm()

