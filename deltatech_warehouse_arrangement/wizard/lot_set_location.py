# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError


class LotChangeLocation(models.TransientModel):
    _name = "lot.change.location"
    _description = "Lot Change Location Wizard"
    _inherit = ["barcodes.barcode_events_mixin"]

    lot_id = fields.Many2one("stock.lot")
    rack_id = fields.Many2one("warehouse.location.rack")
    lot_scanned = fields.Boolean()

    def on_barcode_scanned(self, barcode):
        lot_id = self.env["stock.lot"].search([("name", "=", barcode)])
        if lot_id:
            if len(lot_id) > 1:
                # error, multiple lots found
                pass
            else:
                self.lot_id = lot_id
                self.lot_scanned = True
        else:
            if self.lot_scanned:
                # search for location
                rack_id = self.env["warehouse.location.rack"].search([("barcode", "=", barcode)])
                if not rack_id:
                    raise UserError(_(f"Location {barcode} not found"))
                else:
                    self.rack_id = rack_id
            else:
                # error, lot not found
                raise UserError(_(f"Lot/serial {barcode} not found"))

    def do_change(self):
        if self.lot_id and self.rack_id:
            values = {
                "loc_storehouse_id": self.rack_id.section_id.shelf_id.zone_id.storehouse_id.id,
                "loc_zone_id": self.rack_id.section_id.shelf_id.zone_id.id,
                "loc_shelf_id": self.rack_id.section_id.shelf_id.id,
                "loc_section_id": self.rack_id.section_id.id,
                "loc_rack_id": self.rack_id.id,
            }
            self.lot_id.write(values)

    def reset(self):
        self.rack_id = False
        self.lot_id = False
        self.lot_scanned = False
