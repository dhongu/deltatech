from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    l10n_ro_net_weight = fields.Float()


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_line_weights(self, quantity, uom):
        """Return (gross weight in kg, net weight) for `quantity` expressed in `uom`.

        The quantity is converted to the product unit, and the gross weight is
        converted from the configured weight unit (kg or lb) to kg.
        """
        self.ensure_one()
        if uom and uom != self.uom_id:
            quantity = uom._compute_quantity(quantity, self.uom_id, round=False)
        gross = self.weight * quantity
        weight_uom = self.env["product.template"]._get_weight_uom_id_from_ir_config_parameter()
        kg_uom = self.env.ref("uom.product_uom_kgm")
        if weight_uom != kg_uom:
            gross = weight_uom._compute_quantity(gross, kg_uom, round=False)
        return gross, self.l10n_ro_net_weight * quantity
