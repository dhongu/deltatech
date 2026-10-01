from odoo import fields, models


class StockPickingTransferWizard(models.TransientModel):
    _name = "stock.picking.transfer.wizard"
    _description = "Stock Picking Transfer Wizard"

    # final_dest_location_id = fields.Many2one("stock.location", string="Final Destination Location", required=True)
    operation_id = fields.Many2one(
        "stock.picking.type",
        string="Operation Type",
        required=True,
        domain="[('two_step_transfer_use', '=', 'reception')]",
    )

    def confirm_transfer(self):
        self.ensure_one()
        picking_id = self.env.context.get("active_id")
        if picking_id:
            picking = self.env["stock.picking"].browse(picking_id)
            picking.create_second_transfer_wizard(self.operation_id.default_location_dest_id, self.operation_id)
