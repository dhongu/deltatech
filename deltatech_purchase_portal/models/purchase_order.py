# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    signed_by = fields.Char(string="Signed by", readonly=True, copy=False)
    signed_on = fields.Datetime(string="Signed on", readonly=True, copy=False)
    signature = fields.Binary(string="Signature", readonly=True, copy=False)


    partner_pickup_address_id = fields.Many2one(
        comodel_name='res.partner',
        string="Pickup Address",
        compute='_compute_partner_pickup_address_id',
        store=True, readonly=False, required=True, precompute=True,
        check_company=True,
        index='btree_not_null'
    )


    @api.depends('partner_id')
    def _compute_partner_pickup_address_id(self):
        for order in self:
            if order.partner_id:
                delivery_id = order.partner_id.address_get(['delivery']).get('delivery') or order.partner_id.id
                order.partner_pickup_address_id = delivery_id
            else:
                order.partner_pickup_address_id = False

    def action_preview_purchase_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    vendor_note = fields.Text(string="Vendor Observation")
