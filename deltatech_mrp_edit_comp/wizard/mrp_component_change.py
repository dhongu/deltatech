# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MRPComponentChange(models.TransientModel):
    _name = "mrp.component.change"
    _description = "MRP Component Change "

    product_id = fields.Many2one("product.product")
    product_uom_qty = fields.Float("Quantity", default=1.0, digits="Unit of Measure", required=True)

    @api.model
    def default_get(self, fields_list):
        defaults = super(MRPComponentChange, self).default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        move = self.env["stock.move"].browse(active_id)
        if move.state == "done":
            raise UserError(_("The stock movement status does not allow modification"))
        defaults["product_id"] = move.product_id.id
        defaults["product_uom_qty"] = move.product_uom_qty
        return defaults

    def do_change(self):
        active_id = self.env.context.get("active_id", False)
        move = self.env["stock.move"].browse(active_id)
        # daca la cantitatea move.product_uom_qty factorul este de move.unit_factor
        # self.product_uom_qty  factorul este
        if move.product_uom_qty != 0:
            unit_factor = self.product_uom_qty * move.unit_factor / move.product_uom_qty
        else:
            unit_factor = 0
        move.write(
            {
                "product_id": self.product_id.id,
                "product_uom_qty": self.product_uom_qty,
                "unit_factor": unit_factor,
                "state": "confirmed",
            }
        )
