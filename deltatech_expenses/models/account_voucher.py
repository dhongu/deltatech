# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccountVoucher(models.Model):
    _inherit = "account.move"

    expenses_deduction_id = fields.Many2one("deltatech.expenses.deduction", string="Expenses Deduction", required=False)

    # nu exista metoda in 14.0
    # def voucher_pay_now_payment_create(self):
    #     value = super(AccountVoucher, self).voucher_pay_now_payment_create()
    #     if "expenses_deduction_id" in self.env.context:
    #         value["expenses_deduction_id"] = self.env.context["expenses_deduction_id"]
    #     return value

    def set_paid(self):
        for voucher_to_pay in self:
            if voucher_to_pay.amount_residual == 0.0:
                voucher_to_pay.update({"payment_state": "paid"})
