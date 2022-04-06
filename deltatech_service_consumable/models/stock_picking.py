# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class StockPicking(models.Model):
    _inherit = "stock.picking"

    equipment_id = fields.Many2one("service.equipment", string="Equipment", store=True)
    agreement_id = fields.Many2one(
        "service.agreement", string="Service Agreement", related="equipment_id.agreement_id", store=True, readonly=False
    )

    def check_consumable(self):
        # returns False if all is ok, returns string with error if products exceeds max
        # can be called at picking validation
        self.ensure_one()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        picking_type_id = safe_eval(get_param("service.picking_type_for_service", "False"))
        if not picking_type_id:
            raise UserError(_("Please define the picking type for service."))
        else:
            if self.picking_type_id.id != picking_type_id:
                return ""
            error = ""
            for line in self.move_lines:
                consumable_ids = []
                for cons_item in self.equipment_id.consumable_item_ids:
                    consumable_ids.append(cons_item.product_id)
                if line.product_id in consumable_ids:
                    # find the line in equipment_type
                    agreement_type_consumable = self.env["service.consumable.item"].search(
                        ["&", ("type_id", "=", self.equipment_id.type_id.id), ("product_id", "=", line.product_id.id)]
                    )
                    if not agreement_type_consumable:
                        error = (
                            "Nu a fost gasita in tipul de contract o linie cu consumabilul %s !" % line.product_id.name
                        )
                        return error
                    else:
                        # Find the right consumable in equipment
                        for consumable in self.equipment_id.consumable_item_ids:
                            if consumable.product_id == line.product_id:
                                crt_consumable = consumable
                        crt_consumable = crt_consumable.with_context(equipment_id=self.equipment_id.id)
                        quantity = crt_consumable.quantity
                        if line.location_dest_id.usage == "internal":
                            total_qty = quantity - line.product_uom_qty * agreement_type_consumable.shelf_life
                        else:
                            total_qty = quantity + line.product_uom_qty * agreement_type_consumable.shelf_life
                        if crt_consumable.max_qty < total_qty:
                            error += (
                                "Cantitatea pentru consumabilul "
                                + str(line.product_id.name)
                                + " ("
                                + str(total_qty)
                                + ") este mai mare decat cantitatea maxima permisa ("
                                + str(crt_consumable.max_qty)
                                + ")\r\n"
                            )
            if error and self.state != "done":
                return error

            else:
                return ""
