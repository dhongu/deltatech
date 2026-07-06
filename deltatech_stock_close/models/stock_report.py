# Copyright (C) 2020 NextERP Romania
# Copyright (C) 2020 Terrabit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class StorageSheet(models.TransientModel):
    _inherit = "l10n.ro.stock.storage.sheet"

    only_active = fields.Boolean(default=False)

    def _add_active_filter(self, sql, alias):
        if not self.only_active:
            return sql
        return sql.replace(
            "( %(all_products)s  or sm.product_id in %(product)s )",
            "( %(all_products)s  or sm.product_id in %(product)s ) AND " + alias + ".active = 't'",
        )

    def _add_movement_extra_fields(self, sql):
        sql = sql.replace(
            "categ_id , serial_number )\n        select * from(",
            "categ_id , serial_number, picking_type_id, invoice_date )\n        select * from(",
        )
        sql = sql.replace(
            "categ_id , serial_number)\n\n        select * from(",
            "categ_id , serial_number, picking_type_id, invoice_date)\n\n        select * from(",
        )
        sql = sql.replace(
            "lot_id as serial_number\n            from stock_move as sm",
            "lot_id as serial_number,\n                sp.picking_type_id,\n                am.invoice_date"
            "\n            from stock_move as sm",
        )
        sql = sql.replace(
            "pt.categ_id , lot_id)",
            "pt.categ_id , lot_id, sp.picking_type_id, am.invoice_date)",
        )
        return sql

    def _get_sql_select_sold_init(self):
        sql = super()._get_sql_select_sold_init()
        return self._add_active_filter(sql, "svl")

    def _get_sql_select_sold_final(self):
        sql = super()._get_sql_select_sold_final()
        return self._add_active_filter(sql, "svl")

    def _get_sql_select_in(self):
        sql = super()._get_sql_select_in()
        sql = self._add_movement_extra_fields(sql)
        return self._add_active_filter(sql, "svl_in")

    def _get_sql_select_out(self):
        sql = super()._get_sql_select_out()
        sql = self._add_movement_extra_fields(sql)
        return self._add_active_filter(sql, "svl_out")


class StorageSheetLine(models.TransientModel):
    _inherit = "l10n.ro.stock.storage.sheet.line"

    picking_type_id = fields.Many2one("stock.picking.type", index=True)
    invoice_date = fields.Date(index=True)
