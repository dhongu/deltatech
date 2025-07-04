# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import threading

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _send_order_confirmation_mail(self):
        res = super()._send_order_confirmation_mail()
        if not getattr(threading.current_thread(), "testing", False) and not self.env.registry.in_test_mode():
            sales = self.filtered(
                lambda o: o.company_id.sale_order_sms_post and (o.partner_id.mobile or o.partner_id.phone)
            )
            for sale in sales:
                if sale.state in ["draft", "sale", "cancel"]:
                    continue

                # Sudo as the user has not always the right to read this sms template.
                template = sale.company_id.sudo().sale_order_sms_post_template_id
                sale.with_context(mail_notify_author=True)._message_sms_with_template(
                    template=template,
                    partner_ids=sale.partner_id.ids,
                    put_in_queue=False,
                )
        return res

    def action_confirm(self):
        res = super().action_confirm()

        if getattr(threading.current_thread(), "testing", False) or self.env.registry.in_test_mode():
            return res

        sales = self.filtered(
            lambda p: p.company_id.sale_order_sms_confirm and (p.partner_id.mobile or p.partner_id.phone)
        ).filtered(lambda s: s.state == "sale")

        if not sales:
            return res

        # Salvăm informațiile minime pentru postcommit
        sale_ids = sales.ids


        def _send_sms_after_commit():
            # recreăm env valid după commit
            env = self.env.registry(self.env.cr.dbname).env()
            sales_post = env["sale.order"].browse(sale_ids)

            for sale in sales_post:
                if sale.state != "sale":
                    continue
                template = sale.company_id.sudo().sale_order_sms_confirm_template_id
                sale.with_context(mail_notify_author=True)._message_sms_with_template(
                    template=template,
                    partner_ids=sale.partner_id.ids,
                    put_in_queue=False,
                )

        self.env.cr.postcommit.add(_send_sms_after_commit)
        return res

