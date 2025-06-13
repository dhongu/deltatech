# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    days_send_followup = fields.Integer()
    date_send_followup = fields.Date()

    @api.onchange("date_order", "days_send_followup")
    def _onchange_date_order(self):
        for order in self:
            order.date_send_followup = order.date_order + relativedelta(days=order.days_send_followup)

    @api.model
    def cron_send_followup(self):
        today = date.today()
        domain = [("days_send_followup", ">", 0), ("date_send_followup", "<=", today)]
        orders = self.env["sale.order"].search(domain)
        orders.send_followup()

    def send_followup(self):
        comment_subtype_id = self.env["ir.model.data"]._xmlid_to_res_id("mail.mt_comment")
        for order in self:
            if not order.company_id.sale_followup:
                continue
            template_id = order.company_id.sale_followup_template_id
            if not template_id:
                continue
            message_post = order.with_context(force_send=True).message_post_with_source
            message_post(template_id, email_layout_xmlid="mail.mail_notification_light", subtype_id=comment_subtype_id)

        self.write({"days_send_followup": False, "date_send_followup": False})
