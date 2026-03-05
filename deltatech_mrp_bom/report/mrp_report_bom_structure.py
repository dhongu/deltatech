

from odoo import api,models


class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'


    @api.model
    def get_html(self, bom_id=False, searchQty=1, searchVariant=False):
        if searchVariant:
            product = self.env['product.product'].browse(int(searchVariant))

            domain = [("product_tmpl_id", "=", product.product_tmpl_id.id), ("base_type", "=", "base")]
            base_bom = self.env["mrp.bom"].search(domain, limit=1)
            if base_bom:
                domain = [("product_id", "=",product.id), ("base_type", "=", "derived")]
                derived_bom = self.env["mrp.bom"].search(domain, limit=1)
                if not derived_bom:
                    derived_bom = self.env["mrp.bom"].create(
                        {
                            "product_tmpl_id": product.product_tmpl_id.id,
                            "product_id": product.id,
                            "base_type": "derived",
                        }
                    )
                derived_bom.recompute_from_base()
                bom_id = derived_bom.id

        return super().get_html(bom_id, searchQty, searchVariant)

    @api.model
    def _get_component_data(self, parent_bom, parent_product, warehouse, bom_line, line_quantity, level, index, product_info, ignore_stock=False):
        res = super()._get_component_data(parent_bom, parent_product, warehouse, bom_line, line_quantity, level, index, product_info, ignore_stock)

        return res

