# ©  2008-2021 Deltatech
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProductionLot(models.Model):
    _inherit = "stock.production.lot"

    @api.model_create_multi
    def create(self, vals_list):
        lots = super(ProductionLot, self).create(vals_list)
        equipment_vals_list = []
        for lot in lots:
            if lot.product_id.equi_type_required:
                equipment_vals_list += [
                    {
                        "type_id": lot.product_id.equi_type_id.id,
                        "serial_id": lot.id,
                        "product_id": lot.product_id.equi_type_id,
                        "start_date": fields.Date.today(),
                    }
                ]
        if equipment_vals_list:
            self.env["service.equipment"].create(equipment_vals_list)
        return lots
