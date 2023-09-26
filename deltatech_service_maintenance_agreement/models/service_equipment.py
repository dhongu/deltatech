# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class ServiceEquipment(models.Model):
    _inherit = "service.equipment"

    def get_context_default(self):
        context = super().get_context_default()
        context.update(
            {
                "default_agreement_id": self.agreement_id.id,
                "default_address_id": self.address_id.id,
                "default_contact_id": self.contact_id.id,
            }
        )
        return context
