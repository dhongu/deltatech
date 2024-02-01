# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    acquirer_allowed_ids = fields.Many2many(
        "payment.provider", relation="delivery_carrier_acquirer_allowed_rel", string="Payments Provider Allowed"
    )

    weight_min = fields.Float()
    weight_max = fields.Float()
    logo = fields.Image()
    restrict_label_ids = fields.Many2many("res.partner.category", string="Restrict for partners with label")

    def is_restricted(self, partner_id):
        self.ensure_one()
        for label in self.sudo().restrict_label_ids:
            if label in partner_id.sudo().category_id:
                return True
        return False
