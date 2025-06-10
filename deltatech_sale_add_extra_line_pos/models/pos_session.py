# ©  2024 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result["search_params"]["fields"].append("extra_product_id")
        result["search_params"]["fields"].append("extra_qty")
        return result
