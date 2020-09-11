# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class InventoryChangeDate(models.TransientModel):
    _name = "inventory.change.date"
    _description = "Inventory Change Date"

    date = fields.Datetime(string="Inventory Date")

    @api.model
    def default_get(self, fields_list):
        defaults = super(InventoryChangeDate, self).default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        if active_id:
            inventory = self.env["stock.inventory"].browse(active_id)
            defaults["date"] = inventory.date

        return defaults

    @api.multi
    def do_change(self):
        active_id = self.env.context.get("active_id", False)
        if active_id:
            inventory = self.env["stock.inventory"].browse(active_id)
            inventory.write({"date": self.date})
            # actualizare data la toate miscarile de stoc
            inventory.move_ids.write({"date": self.date})
