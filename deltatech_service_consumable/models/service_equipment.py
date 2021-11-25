# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
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

        context = {
            "default_equipment_id": self.id,
            "default_agreement_id": self.agreement_id.id,
            "default_picking_type_code": "outgoing",
            "default_picking_type_id": picking_type_id,
            "default_partner_id": self.address_id.id,
        }

        if self.consumable_item_ids:
            context["default_move_lines"] = []
            for item in self.consumable_item_ids:
                value = {"product_id": item.product_id.id}
                context["default_move_lines"] += [(0, 0, value)]

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
