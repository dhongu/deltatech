# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import RedirectWarning
from odoo.tools.safe_eval import safe_eval


class ServiceEquipment(models.Model):
    _inherit = "service.equipment"

    consumable_item_ids = fields.Many2many(
        "service.consumable.item", string="Consumables", compute="_compute_consumable_item_ids", readonly=True
    )

    def _compute_consumable_item_ids(self):
        for equipment in self:
            domain = [("type_id", "=", equipment.type_id.id)]
            equipment.consumable_item_ids = self.env["service.consumable.item"].search(domain)

    def new_piking_button(self):
        # todo: de pus in config daca livrarea se face la adresa din echipamente sau contract

        get_param = self.env["ir.config_parameter"].sudo().get_param
        picking_type_id = safe_eval(get_param("service.picking_type_for_service", "False"))
        picking_type = self.env["stock.picking.type"].browse(picking_type_id)
        context = {
            "default_equipment_id": self.id,
            "default_agreement_id": self.agreement_id.id,
            "default_picking_type_code": "outgoing",
            "default_picking_type_id": picking_type_id,
            "default_partner_id": self.address_id.id,
        }

        if self.consumable_item_ids:
            context["default_move_ids_without_package"] = []
            for item in self.consumable_item_ids:
                value = {
                    "name": item.product_id.name,
                    "product_id": item.product_id.id,
                    "product_uom": item.product_id.uom_id.id,
                    "product_uom_qty": 1,
                    "location_id": picking_type.default_location_src_id.id,
                    "location_dest_id": picking_type.default_location_dest_id.id,
                    "price_unit": item.product_id.standard_price,
                }
                context["default_move_ids_without_package"] += [(0, 0, value)]

        return {
            "name": _("Delivery for service"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.picking",
            "view_id": False,
            "views": [[False, "form"]],
            "context": context,
            "type": "ir.actions.act_window",
        }

    def delivered_button(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        picking_type_id = safe_eval(get_param("service.picking_type_for_service", "False"))

        if not picking_type_id:
            action = self.env.ref("stock.action_stock_config_settings")
            raise RedirectWarning(_("Please define the picking type for service."), action.id, _("Stock Settings"))

        domain = [("equipment_id", "in", self.ids), ("picking_type_id", "=", picking_type_id)]
        pickings = self.env["stock.picking"].sudo().search(domain)
        move_lines = self.env["stock.move"].sudo().search([("picking_id", "in", pickings.ids)])
        # view_id = self.sudo().env.ref('terrabit_rsy.view_stock_move_tree_rsy').id
        return {
            "domain": [("id", "in", move_lines.ids)],
            "name": _("Delivery for service"),
            "view_type": "form",
            "view_mode": "tree",
            "res_model": "stock.move",
            # 'view_id': view_id,
            # 'context': context,
            "type": "ir.actions.act_window",
        }

    def picking_button(self):

        get_param = self.env["ir.config_parameter"].sudo().get_param
        picking_type_id = safe_eval(get_param("service.picking_type_for_service", "False"))

        pickings = self.env["stock.picking"].search([("equipment_id", "in", self.ids)])
        context = {
            "default_equipment_id": self.id,
            "default_agreement_id": self.agreement_id.id,
            "default_picking_type_code": "outgoing",
            "default_picking_type_id": picking_type_id,
            "default_partner_id": self.address_id.id,
        }

        return {
            "domain": "[('id','in', [" + ",".join(map(str, pickings.ids)) + "])]",
            "name": _("Delivery for service"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "stock.picking",
            "view_id": False,
            "context": context,
            "type": "ir.actions.act_window",
        }
