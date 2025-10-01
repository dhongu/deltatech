from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _load_pos_data_fields(self, config_id):
        data_fields = super()._load_pos_data_fields(config_id)
        return data_fields + ["extra_product_id", "extra_percent", "extra_qty"]
