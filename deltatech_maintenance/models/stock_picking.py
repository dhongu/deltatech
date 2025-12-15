# ©  2008-2022  Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from markupsafe import Markup


class StockPicking(models.Model):
    _inherit = "stock.picking"

    request_id = fields.Many2one("maintenance.request", string="Maintenance Request")
    equipment_id = fields.Many2one("maintenance.equipment", string="Equipment")

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        for picking in pickings:
            if picking.request_id:
                # Use Odoo's internal record link markup so the frontend renders a clickable link
                # and opens the related record in a dialog or form view.
                link = (
                    f'<a href="#" data-oe-model="stock.picking" data-oe-id="{picking.id}">'  # noqa: B950
                    f"{picking.display_name}</a>"
                )
                picking.request_id.message_post(
                    body=Markup(
                        f"Created stock picking {link} for this maintenance request."
                    ),
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                )
        return pickings
