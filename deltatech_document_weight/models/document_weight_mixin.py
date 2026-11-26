from odoo import api, models


class DocumentWeightMixin(models.AbstractModel):
    _name = "deltatech.document.weight.mixin"
    _description = "Weights and volume on printed documents"

    @api.model
    def _get_document_weight_labels(self):
        template = self.env["product.template"]
        return {
            "weight": template._get_weight_uom_name_from_ir_config_parameter(),
            "volume": template._get_volume_uom_name_from_ir_config_parameter(),
        }

    @api.model
    def _sum_document_weights(self, entries):
        """Totals for ``entries``: (product, quantity, uom) tuples. Lines without a product are skipped."""
        totals = {"net": 0.0, "gross": 0.0, "volume": 0.0}
        for product, quantity, uom in entries:
            if not product:
                continue
            for key, value in product._get_document_weights(quantity, uom).items():
                totals[key] += value
        return totals
