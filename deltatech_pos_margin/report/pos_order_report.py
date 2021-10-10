# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

# from odoo import fields, models

# in 15 exista deja campul
# class PosOrderReport(models.Model):
#     _inherit = "report.pos.order"
#
#     margin = fields.Float(string="Margin")
#
#     def _select(self):
#         sql_select = super(PosOrderReport, self)._select()
#         return (
#             sql_select
#             + ",SUM(l.margin / CASE COALESCE(s.currency_rate, 0) "
#             + " WHEN 0 THEN 1.0 ELSE s.currency_rate END) AS margin"
#         )
