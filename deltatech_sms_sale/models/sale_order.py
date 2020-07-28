# -*- coding: utf-8 -*-
# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, _

import threading


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_quotation_send(self):
        res = super(SaleOrder, self).action_quotation_send()
        if not getattr(threading.currentThread(), 'testing', False) and not self.env.registry.in_test_mode():
            sales = self.filtered(
                lambda p: p.company_id.sale_order_sms_post and (p.partner_id.mobile or p.partner_id.phone))
            for sale in sales:
                # Sudo as the user has not always the right to read this sms template.
                template = sale.company_id.sudo().sale_order_sms_post_template_id
                sale._message_sms_with_template(
                    template=template,
                    partner_ids=sale.partner_id.ids,
                    put_in_queue=False
                )

        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if not getattr(threading.currentThread(), 'testing', False) and not self.env.registry.in_test_mode():
            sales = self.filtered(
                lambda p: p.company_id.sale_order_sms_confirm and (p.partner_id.mobile or p.partner_id.phone))
            for sale in sales:
                # Sudo as the user has not always the right to read this sms template.
                template = sale.company_id.sudo().sale_order_sms_confirm_template_id
                sale._message_sms_with_template(
                    template=template,
                    partner_ids=sale.partner_id.ids,
                    put_in_queue=False
                )
        return res
