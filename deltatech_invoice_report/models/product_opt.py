# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details


# from odoo import fields, models
#
#
# class ProductInvoiceHistory(models.Model):
#     _name = "product.invoice.history"
#     _description = "product.invoice.history"
#
#     product_id = fields.Many2one("product.product")
#     template_id = fields.Many2one("product.template", index=True)
#     year = fields.Char(string="Year")
#     qty_in = fields.Float(string="Qty In", digits="Product Unit of Measure")
#     qty_out = fields.Float(string="Qty Out", digits="Product Unit of Measure")
#
#
# class ProductTemplate(models.Model):
#     _inherit = "product.template"
#
#     invoice_count = fields.Integer(compute="_compute_invoice_count")
#     invoice_history = fields.One2many(
#         "product.invoice.history", "template_id", compute="_compute_invoice_history", store=True
#     )
#     last_invoice_history_computed = fields.Datetime(string="Last Computed Invoice History")
#     last_sale_date = fields.Date()
#
#     def refresh_invoice_history(self):
#         self._compute_invoice_history()
#         self.write({"last_invoice_history_computed": fields.Datetime.now()})
#
#     def _compute_invoice_history(self):
#         domain = [("template_id", "in", self.ids)]
#         invoice_history = self.env["product.invoice.history"].search(domain)
#         invoice_history.unlink()
#
#         domain = [
#             ("move_type", "in", ["out_invoice", "out_refund"]),
#             ("product_tmpl_id", "in", self.ids),
#         ]
#         groups_out = self.env["account.invoice.report"].read_group(
#             domain=domain,
#             fields=["product_tmpl_id, quantity", "invoice_date"],
#             groupby=["product_tmpl_id, invoice_date:year"],
#         )
#
#         domain = [
#             ("move_type", "in", ["in_invoice", "in_refund"]),
#             ("product_tmpl_id", "in", self.ids),
#         ]
#         groups_in = self.env["account.invoice.report"].read_group(
#             domain=domain,
#             fields=["product_tmpl_id", "quantity", "invoice_date"],
#             groupby=["product_tmpl_id, invoice_date:year"],
#         )
#
#         history = {}
#         for item in groups_out:
#             key = (item["product_tmpl_id"][0], item["invoice_date:year"])
#             history[key] = {
#                 "template_id": item["product_tmpl_id"][0],
#                 "year": item["invoice_date:year"],
#                 "qty_out": item["quantity"],
#             }
#
#         for item in groups_in:
#             key = (item["product_tmpl_id"][0], item["invoice_date:year"])
#             if key in history:
#                 history[key]["qty_in"] = -1 * item["quantity"]
#             else:
#                 history[key] = {
#                     "template_id": item["product_tmpl_id"][0],
#                     "year": item["invoice_date:year"],
#                     "qty_in": -1 * item["quantity"],
#                 }
#         history_values = []
#         for key in history:
#             history_values += [history[key]]
#         self.env["product.invoice.history"].create(history_values)
#
#     def _compute_invoice_count(self):
#         for template in self:
#             products = template.product_variant_ids
#
#             domain = [
#                 ("move_type", "in", ["out_invoice", "out_refund"]),
#                 ("product_id", "in", products.ids),
#             ]
#             product_qty = 0
#             price_average = 0.0
#             groups = self.env["account.invoice.report"].read_group(
#                 domain=domain, fields=["product_id", "product_qty", "price_average"], groupby=["product_id"]
#             )
#             for item in groups:
#                 product_qty += item["product_qty"]
#                 price_average = item["price_average"]
#
#             template.invoice_count = price_average
#
#     def action_view_invoice(self):
#         action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_invoice_report_all")
#         products = self.env["product.product"]
#         for template in self:
#             products |= template.product_variant_ids
#         action["context"] = {
#             "group_by": ["date:year"],
#             "measures": ["product_qty", "price_average"],
#             "col_group_by": ["move_type"],
#             "group_by_no_leaf": 1,
#             "search_disable_custom_filters": True,
#         }
#         action["domain"] = [("move_type", "in", ["out_invoice", "out_refund"]), ("product_id", "in", products.ids)]
#         return action
#
#
# class ProductProduct(models.Model):
#     _inherit = "product.product"
#
#     def action_view_invoice(self):
#         action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_invoice_report_all")
#         action[
#             "context"
#         ] = """{
#              'group_by':['date:year'],
#              'measures': ['product_qty', 'price_average'],
#              'col_group_by': ['move_type'] ,
#               'group_by_no_leaf': 1,
#               'search_disable_custom_filters': True
#              }"""
#         #
#         action["domain"] = [("move_type", "in", ["out_invoice", "out_refund"]), ("product_id", "in", self.ids)]
#         return action
