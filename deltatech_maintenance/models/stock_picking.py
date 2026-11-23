# ©  2008-2022  Deltatech
# See README.rst file on addons root folder for license details

from markupsafe import Markup

from odoo import api, fields, models


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
                # Markup.format() escapes display_name, so it cannot inject HTML in the chatter.
                link = Markup('<a href="#" data-oe-model="stock.picking" data-oe-id="{}">{}</a>').format(
                    picking.id, picking.display_name
                )
                picking.request_id.message_post(
                    body=Markup("Created stock picking {} for this maintenance request.").format(link),
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                )
        return pickings
