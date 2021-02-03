# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.constrains("seller_ids", "purchase_ok")
    def _check_description(self):
        if self.purchase_ok and self.type == "product":
            if not self.seller_ids:
                raise ValidationError(_("No defined a supplier of this product"))
