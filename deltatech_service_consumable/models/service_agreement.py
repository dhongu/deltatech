# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.tools.safe_eval import safe_eval


class ServiceAgreement(models.Model):
    _inherit = "service.agreement"

    total_costs = fields.Float(string="Total Cost", readonly=True)  # se va calcula din suma avizelor
    total_percent = fields.Float(string="Total percent", readonly=True)  # se va calcula (consum/factura)*100

    def picking_button(self):
        self.ensure_one()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        picking_type_id = safe_eval(get_param("service.picking_type_for_service", "False"))

        pickings = self.env["stock.picking"].search([("agreement_id", "in", self.ids), ("state", "=", "done")])
        context = {
            "default_agreement_id": self.id,
            "default_picking_type_code": "outgoing",
            "default_picking_type_id": picking_type_id,
            "default_state": "done",
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

    def compute_costs(self):
        """
        Used to recompute costs from pickings, if necessary.
        The costs are added at each picking validation, if the picking has the
        picking_type_for_service type (see button_validate function)
        :return: nothing
        """
        get_param = self.env["ir.config_parameter"].sudo().get_param
        picking_type_id = safe_eval(get_param("service.picking_type_for_service", "False"))
        for agreement in self:
            partners = self.env["res.partner"]
            partners |= agreement.partner_id
            if agreement.partner_id.child_ids:
                for child in agreement.partner_id.child_ids:
                    partners |= child
            pickings = self.env["stock.picking"].search(
                [
                    ("agreement_id", "=", agreement.id),
                    ("picking_type_id", "=", picking_type_id),
                    ("picking_type_code", "=", "outgoing"),
                    ("state", "=", "done"),
                    ("partner_id", "in", partners.ids),
                ]
            )
            svls = pickings.move_ids.stock_valuation_layer_ids
            value = 0.0
            for svl in svls:
                value += svl.value
            agreement.write({"total_costs": value})

    def compute_percent(self):
        for agreement in self:
            if agreement.total_invoiced:
                total_percent = round(((-1 * agreement.total_costs) / agreement.total_invoiced) * 100, 2)
            else:
                total_percent = 0.0
            agreement.write({"total_percent": total_percent})
