# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    request_number = fields.Char(string="Request Number")

    def action_get_number(self):
        if not self.request_number:
            if self.picking_type_id.request_sequence_id:
                request_number = self.picking_type_id.request_sequence_id.next_by_id()
                if request_number:
                    self.write({"request_number": request_number, "name": request_number})

    def unlink(self):
        for picking in self:
            if picking.request_number:
                raise UserError(_("The document %s has been numbered") % picking.request_number)
        return super(StockPicking, self).unlink()


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    request_sequence_id = fields.Many2one("ir.sequence", string="Sequence on Request")
