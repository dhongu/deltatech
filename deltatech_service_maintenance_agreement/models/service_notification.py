# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ServiceNotification(models.Model):
    _inherit = "service.notification"

    emplacement = fields.Char(string="Emplacement", related=False, readonly=True)
    agreement_id = fields.Many2one(
        "service.agreement",
        string="Service Agreement",
        related="equipment_id.agreement_id",
        readonly=True,
    )
    can_create_delivery = fields.Boolean(related="agreement_id.type_id.permits_pickings")

    @api.model
    def create(self, vals):
        equipment_id = vals.get("equipment_id", False)

        if equipment_id:
            equipment = self.env["service.equipment"].browse(equipment_id)
            if not vals.get("agreement_id", False):
                vals["agreement_id"] = equipment.agreement_id.id

        return super().create(vals)

    def get_context_default(self):
        context = super().get_context_default()
        context.update(
            {
                "default_agreement_id": self.agreement_id.id,
            }
        )
        return context
