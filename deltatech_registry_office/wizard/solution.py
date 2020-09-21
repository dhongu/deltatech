# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, Warning, except_orm

from ..models import registry_office_common


class RegistryOfficSolution(models.TransientModel):
    _name = "registry.office.solution"
    _description = "Solution"

    state = fields.Selection(registry_office_common.selection_solution, default="new", string="Status")

    resolution = fields.Text()
    recipient_id = fields.Many2one("res.partner", string="Recipient")  # Destinatar

    with_shipment = fields.Boolean()
    shipment_pertner_id = fields.Many2one("res.partner", string="Shipped by")  # expediata de
    shipment_note = fields.Char("Shipment Note")
    shipment_id = fields.Many2one("registry.office.shipment")

    @api.multi
    def do_solution(self):
        active_ids = self.env.context.get("active_ids", False)
        docs = self.env["registry.office.doc"].browse(active_ids)
        docs.filtered(lambda r: r.user_id == self.env.user.id and r.state == "progress")

        # determianre user responsabil in functie de departament

        for doc in docs:
            values = {"state": self.state}
            if self.with_shipment:
                values.update(
                    {
                        "shipment_pertner_id": self.shipment_pertner_id,
                        "shipment_note": self.shipment_note,
                        "shipment_id": self.shipment_id,
                    }
                )
            doc.write(values)
