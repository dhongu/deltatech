# Copyright (C) 2020 NextERP Romania
# Copyright (C) 2020 Terrabit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StorageSheet(models.TransientModel):
    _inherit = "l10n.ro.stock.storage.sheet"

    only_active = fields.Boolean(default=False)

    def _get_sql_select_sold_init(self):
        sql = super()._get_sql_select_sold_init()
        if self.only_active:
            sql = sql.replace(
                "left join stock_valuation_layer as svl on svl.stock_move_id = sm.id and",
                "left join stock_valuation_layer as svl on svl.stock_move_id = sm.id and svl.active = 't' and",
            )
        return sql

    def _get_sql_select_sold_final(self):
        sql = super()._get_sql_select_sold_final()
        if self.only_active:
            sql = sql.replace(
                "left join stock_valuation_layer as svl on svl.stock_move_id = sm.id and",
                "left join stock_valuation_layer as svl on svl.stock_move_id = sm.id and svl.active = 't' and",
            )
        return sql

    def _get_sql_select_in(self):
        sql = super()._get_sql_select_in()
        if self.only_active:
            sql = sql.replace(
                "left join stock_valuation_layer as svl on svl.stock_move_id = sm.id and",
                "left join stock_valuation_layer as svl on svl.stock_move_id = sm.id and svl.active = 't' and",
            )
        return sql

    def _get_sql_select_out(self):
        sql = super()._get_sql_select_out()
        if self.only_active:
            sql = sql.replace(
                "left join stock_valuation_layer as svl on svl.stock_move_id = sm.id and",
                "left join stock_valuation_layer as svl on svl.stock_move_id = sm.id and svl.active = 't' and",
            )
        return sql


# class StorageSheetLine(models.TransientModel):
#     _inherit = "l10n.ro.stock.storage.sheet.line"
#
#     picking_type_id = fields.Many2one("stock.picking.type", index=True)
#     invoice_date = fields.Date(index=True)
