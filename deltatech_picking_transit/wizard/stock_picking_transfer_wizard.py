from odoo import fields, models


class StockPickingTransferWizard(models.TransientModel):
    _name = "stock.picking.transfer.wizard"
    _description = "Stock Picking Transfer Wizard"

    final_dest_location_id = fields.Many2one("stock.location", string="Final Destination Location", required=True)

    def confirm_transfer(self):
        self.ensure_one()
        picking_id = self.env.context.get("active_id")
        if picking_id:
            picking = self.env["stock.picking"].browse(picking_id)
            picking.create_second_transfer_wizard(
                self.final_dest_location_id, picking.picking_type_id.next_operation_id
            )
