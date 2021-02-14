# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ServiceEquiAgreement(models.TransientModel):
    _name = "service.equi.agreement"
    _description = "Service Equipment Agreement"

    equipment_id = fields.Many2one("service.equipment", string="Equipment", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Customer", required=True, domain=[("customer", "=", True)])
    agreement_id = fields.Many2one(
        "service.agreement",
        string="Contract Service",
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super(ServiceEquiAgreement, self).default_get(fields_list)

        active_id = self.env.context.get("active_id", False)
        if active_id:
            defaults["equipment_id"] = active_id
            equipment = self.env["service.equipment"].browse(active_id)
            defaults["partner_id"] = equipment.partner_id.id
            agreement = self.env["service.agreement"].search([("partner_id", "=", equipment.partner_id.id)], limit=1)
            if agreement:
                defaults["agreement_id"] = agreement.id
        else:
            raise UserError(_("Please select equipment."))
        return defaults

    def do_agreement(self):
        if not self.agreement_id:
            cycle = self.env.ref("deltatech_service.cycle_monthly")
            values = {"partner_id": self.partner_id.id, "cycle_id": cycle.id}
            self.agreement_id = self.env["service.agreement"].create(values)

        # self.equipment_id.write({'agreement_id':self.agreement_id.id,
        #                         'partner_id':self.partner_id.id})
        for template in self.equipment_id.type_id.template_meter_ids:
            values = {
                "agreement_id": self.agreement_id.id,
                "equipment_id": self.equipment_id.id,
                "currency_id": template.currency_id.id,
                "product_id": template.product_id.id,
                "analytic_account_id": template.analytic_account_id.id,
            }
            for meter in self.equipment_id.meter_ids:
                if meter.meter_categ_id == template.meter_categ_id:
                    values["meter_id"] = meter.id
                    values["uom_id"] = template.meter_categ_id.bill_uom_id.id

            self.env["service.agreement.line"].create(values)

        action = {
            "domain": "[('id','=',%s)]" % self.agreement_id.id,
            "name": _("Service Agreement"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "service.agreement",
            "view_id": False,
            "type": "ir.actions.act_window",
            "res_id": self.agreement_id.id,
        }
        return action
