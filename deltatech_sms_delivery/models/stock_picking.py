# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import threading

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_sms_preparation(self):

        if not getattr(threading.currentThread(), "testing", False) and not self.env.registry.in_test_mode():
            pickings = self.filtered(
                lambda p: p.company_id.delivery_sms_preparation and (p.partner_id.mobile or p.partner_id.phone)
            )
            for picking in pickings:
                # Sudo as the user has not always the right to read this sms template.
                template = picking.company_id.sudo().delivery_sms_preparation_template_id
                picking.with_context(mail_notify_author=True)._message_sms_with_template(
                    template=template, partner_ids=picking.partner_id.ids, put_in_queue=False
                )

    def action_sms_ready(self):

        if not getattr(threading.currentThread(), "testing", False) and not self.env.registry.in_test_mode():
            pickings = self.filtered(
                lambda p: p.company_id.delivery_sms_ready and (p.partner_id.mobile or p.partner_id.phone)
            )
            for picking in pickings:
                # Sudo as the user has not always the right to read this sms template.
                template = picking.company_id.sudo().delivery_sms_ready_template_id
                picking.with_context(mail_notify_author=True)._message_sms_with_template(
                    template=template, partner_ids=picking.partner_id.ids, put_in_queue=False
                )
