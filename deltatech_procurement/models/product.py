# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.constrains("seller_ids", "purchase_ok")
    def _check_description(self):
        if self.purchase_ok and self.type == "product":
            if not self.seller_ids:
                get_param = self.env["ir.config_parameter"].sudo().get_param
                required_supplier = safe_eval(get_param("product.required_supplier", "False"))
                if required_supplier:
                    raise ValidationError(_("No defined a supplier of this product"))
