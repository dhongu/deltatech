from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _load_pos_data_fields(self, config_id):
        result = super()._load_pos_data_fields(config_id)
        config = self.env["pos.config"].browse(config_id)
        if config.display_stock:
            result.extend(["qty_available", "is_storable"])
        return result

    def _load_pos_data(self, data):
        config = self.env["pos.config"].browse(data["pos.config"]["data"][0]["id"])
        if config.display_stock and config.warehouse_id:
            self = self.with_context(warehouse_id=config.warehouse_id.id)
        return super()._load_pos_data(data)
