# # ©  2015-2019 Deltatech
# # See README.rst file on addons root folder for license details
#
#
# from odoo import  fields, models
#
#
# class ExpensesDeductionFromAccountVoucher(models.TransientModel):
#     _name = "expenses.deduction.from.account.voucher"
#     _description = "Create Expenses Deduction"
#
#     def _get_date_expense(self):
#         if context is None:
#             context = {}
#         voucher_pool = self.pool.get("account.voucher")
#         active_id = context and context.get("active_id", [])
#         voucher = voucher_pool.browse(cr, uid, active_id, context)
#         return voucher and voucher.date
#
#     date_expense = fields.date("Expense Date", default=_get_date_expense)
#
#     def create_expenses_deduction(self):
#         # trebuie sa citesc datele si sa intru in moul de creare
#         data_pool = self.pool.get("ir.model.data")
#         voucher_pool = self.pool.get("account.voucher")
#         action_model, action_id = data_pool.get_object_reference(
#             cr, uid, "deltatech_expenses", "action_deltatech_expenses_deduction"
#         )
#         action_pool = self.pool.get(action_model)
#         action = action_pool.read(cr, uid, action_id, context=context)
#         res_ids = context and context.get("active_ids", [])
#         expenses_pool = self.pool.get("deltatech.expenses.deduction")
#         for expense in self.browse(cr, uid, ids, context):
#             date_expense = expense.date_expense
#         expenses_id = expenses_pool.create(cr, uid, {"date_expense": date_expense}, context)
#         voucher_ids = []
#         for voucher in voucher_pool.browse(cr, uid, res_ids, context):
#             if not voucher.expenses_deduction_id:
#                 voucher_ids.append(voucher.id)
#         voucher_pool.write(cr, uid, voucher_ids, {"expenses_deduction_id": expenses_id}, context)
#         action["domain"] = "[('id','in', [" + str(expenses_id) + "])]"
#         return action
#
#
#
