from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _load_pos_data_fields(self, config):
        # În 19.0 cardul de produs din POS primește un `product.template`,
        # așa că stocul trebuie încărcat pe șablon, nu pe variantă.
        result = super()._load_pos_data_fields(config)
        if config.display_stock and "qty_available" not in result:
            result = result + ["qty_available"]
        return result

    @api.model
    def _load_pos_data_read(self, records, config):
        if config.display_stock and config.warehouse_id:
            records = records.with_context(warehouse_id=config.warehouse_id.id)
        return super()._load_pos_data_read(records, config)
