# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockInventoryMerge(models.TransientModel):
    _name = "stock.inventory.merge"
    _description = "Stock Inventory Merge Wizard"

    name = fields.Char(required=True)
    date = fields.Datetime(required=True, default=fields.Datetime.now())
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    location_id = fields.Many2one("stock.location")

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if "company_id" in defaults and defaults["company_id"]:
            warehouse_id = self.env["stock.warehouse"].search([("company_id", "=", defaults["company_id"])], limit=1)
        else:
            warehouse_id = self.env["stock.warehouse"].search([], limit=1)
        defaults["location_id"] = warehouse_id.lot_stock_id.id
        defaults["name"] = "/"
        return defaults

    def merge_inventory(self):
        active_ids = self.env.context.get("active_ids", False)
        if not active_ids:
            raise UserError(_("You must select at least two inventory documents"))
        inventories = self.env["stock.inventory"].browse(active_ids)
        if len(inventories) < 2:
            raise UserError(_("You must select at least two inventory documents"))

        not_done = inventories.filtered(lambda s: s.state != "done")
        if not_done:
            raise UserError(_("All inventories must be in done state to be merged"))

        # create inventory
        if not self.name or self.name == "/":
            sequence = self.env.ref("deltatech_stock_inventory.sequence_inventory_doc")
            if sequence:
                inventory_name = sequence.next_by_id()
        else:
            inventory_name = self.name

        location_ids = []
        if self.location_id:
            locations_to_append = (4, self.location_id.id)
            location_ids.append(locations_to_append)
        else:
            for inventory in inventories:
                for location in inventory.location_ids:
                    locations_to_append = (4, location.id)
                    location_ids.append(locations_to_append)
        vals = {
            "name": inventory_name,
            "date": self.date,
            "company_id": self.company_id.id,
            "location_ids": location_ids,
            "state": "done",  # already checked if all components in done state
        }
        result_inventory = self.env["stock.inventory"].create(vals)

        # move inventory lines and stock moves to the new inventory
        old_inventory_names = []
        for inventory in inventories:
            inventory.line_ids.write({"inventory_id": result_inventory.id})
            inventory.move_ids.write({"inventory_id": result_inventory.id})
            old_inventory_names.append(inventory.name)
            inventory.with_context(merge_inventory=True).unlink()

        message = _("User %(user_name)s has merged inventories %(inventory_names)s") % {
            "user_name": self.env.user.name,
            "inventory_names": ", ".join(old_inventory_names),
        }
        result_inventory.message_post(body=message)
        action = {
            "name": _("Merged inventory"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "views": [(False, "form")],
            "res_model": "stock.inventory",
            "res_id": result_inventory.id,
        }
        return action
