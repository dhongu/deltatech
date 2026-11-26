from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    # Same definition as in l10n_ro_stock and l10n_ro_stock_base: whichever of them is installed,
    # it is the same field and the same column.
    l10n_ro_net_weight = fields.Float("Net Weight", digits="Stock Weight")

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form":
            self.env["product.template"]._document_weight_remove_duplicates(arch)
        return arch, view

    def _get_document_weights(self, quantity, uom=None):
        """Net weight, gross weight and volume of ``quantity`` units of the product.

        :param quantity: quantity expressed in ``uom``
        :param uom: unit of measure of the quantity (the product unit if empty)
        :return: dict with the keys ``net``, ``gross`` and ``volume``, in the weight and volume units
            of the database (see ``_get_document_weight_labels``)
        """
        self.ensure_one()
        if uom and uom != self.uom_id:
            quantity = uom._compute_quantity(quantity, self.uom_id, round=False)
        return {
            "net": self.l10n_ro_net_weight * quantity,
            "gross": self.weight * quantity,
            "volume": self.volume * quantity,
        }
