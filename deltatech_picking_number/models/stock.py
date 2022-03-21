# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    request_number = fields.Char(string="Request Number")
    force_number = fields.Boolean(related="picking_type_id.request_sequence_force")

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

    def button_validate(self):
        result = super(StockPicking, self).button_validate()
        for picking in self:
            if picking.force_number:
                number = picking.picking_type_id.request_sequence_id.next_by_id()
                self.write({"request_number": number, "name": number})
        return result


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    request_sequence_id = fields.Many2one("ir.sequence", string="Sequence on Request")
    request_sequence_force = fields.Boolean(
        "Force request sequence",
        help="For pickings of this type, the request sequence will be forced in number field at picking validation",
    )
