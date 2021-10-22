# ©  2008-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductReplenish(models.TransientModel):
    _inherit = "product.replenish"

    supplier_id = fields.Many2one("product.supplierinfo")

    def _prepare_run_values(self):
        values = super(ProductReplenish, self)._prepare_run_values()
        values["supplier_id"] = self.supplier_id
        return values
