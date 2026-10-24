from odoo import models


class Website(models.Model):
    _inherit = "website"

    def _get_product_sort_mapping(self):
        rem = super()._get_product_sort_mapping()

        filtered = [
            item for item in rem
            if 'date' not in item[0] and 'id' not in item[0]
        ]

        return filtered
