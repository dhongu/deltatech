# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import RedirectWarning
from odoo.tools.safe_eval import safe_eval


class ServiceConsumableItem(models.Model):
    _name = "service.consumable.item"
    _description = "Consumable Item"

    name = fields.Char(string="Name", related="product_id.name")
    type_id = fields.Many2one("service.equipment.type", string="Type", ondelete="cascade")
    product_id = fields.Many2one(
        "product.product", string="Consumable", ondelete="restrict", domain=[("type", "=", "product")]
    )
    quantity = fields.Float(string="Quantity", compute="_compute_quantity", digits="Product Unit of Measure")
    shelf_life = fields.Float(string="Shelf Life", related="product_id.shelf_life")
    uom_shelf_life = fields.Many2one(string="Shelf Life UoM", related="product_id.uom_shelf_life")
    colors = fields.Char("HTML Colors Index", default="['#a9d70b', '#f9c802', '#ff0000']")
    max_qty = fields.Float(string="Quantity Max", digits="Product Unit of Measure", help="Maximum Quantity allowed")

    def _compute_quantity(self):

        get_param = self.env["ir.config_parameter"].sudo().get_param
        picking_type_id = safe_eval(get_param("service.picking_type_for_service", "False"))

        if not picking_type_id:
            action = self.env.ref("stock.action_stock_config_settings").sudo()
            raise RedirectWarning(_("Please define the picking type for service."), action.id, _("Stock Settings"))

        equipment_id = self.env.context.get("equipment_id", False)
        pickings = self.env["stock.picking"]

        if equipment_id:
            domain = [
                ("equipment_id", "=", equipment_id),
                ("picking_type_id", "=", picking_type_id),
                ("state", "=", "done"),
            ]
            pickings = self.env["stock.picking"].sudo().search(domain)

        for item in self:
            if equipment_id:
                domain = [("picking_id", "in", pickings.ids), ("product_id", "=", item.product_id.id)]

                move_lines = self.env["stock.move"].sudo().search(domain)
                move_qtys = 0.0
                for move in move_lines:
                    if move.location_dest_id.usage == "internal":
                        move_qtys += -move.product_id.shelf_life * move.product_uom_qty
                    else:
                        move_qtys += move.product_id.shelf_life * move.product_uom_qty

                eff = self.env["service.efficiency.report"]
                domain = [("product_id", "=", item.product_id.id), ("equipment_id", "=", equipment_id)]
                fields_list = ["equipment_id", "product_id", "location_dest_id", "usage", "shelf_life"]
                group_by_list = ["equipment_id", "product_id", "location_dest_id"]
                res = eff.read_group(domain=domain, fields=fields_list, groupby=group_by_list, lazy=False)
                usage = 0.0
                for line in res:
                    usage = line["usage"]
                item.quantity = move_qtys - usage
