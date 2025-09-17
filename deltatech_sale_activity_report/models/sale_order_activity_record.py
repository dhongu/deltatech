# models/sale_order_activity_record.py
from odoo import fields, models


class SaleOrderActivityRecord(models.Model):
    _name = "sale.order.activity.record"
    _description = "Sale Order Activity Record"

    sale_order_id = fields.Many2one("sale.order", string="Sale Order", required=True, ondelete="cascade")
    change_date = fields.Date(string="Change Date", default=fields.Datetime.now, required=True)
    state = fields.Selection(
        selection=[
            ("draft", "Quotation"),
            ("sent", "Quotation Sent"),
            ("sale", "Sales Order"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ],
        string="State",
    )

    # ('change_date', '&gt;=', (context_today()-relativedelta(days=60)).strftime('%Y-%m-%d'))
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user, required=True)
    stage = fields.Selection(
        [
            ("placed", "Placed"),  # comanda plasta pe website
            ("in_process", "In Process"),  # comanda in procesare de catre agentul de vanzare
            ("waiting", "Waiting availability"),  # nu sunt in stoc toate produsele din comanda
            ("postponed", "Postponed"),  # livrarea a fost amanata
            ("to_be_delivery", "To Be Delivery"),  # comanda este de livrat
            ("in_delivery", "In Delivery"),  # marfa a fost predata la curier
            ("delivered", "Delivered"),  # comanda a fost livrata la client
            ("canceled", "Canceled"),
            ("returned", "Returned"),
        ],
        string="Stage",
    )
