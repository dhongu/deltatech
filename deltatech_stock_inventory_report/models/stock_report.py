# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class StorageSheet(models.TransientModel):
    _inherit = "l10n.ro.stock.storage.sheet"

    def _get_sql_select_sold_final(self):
        sql = super()._get_sql_select_sold_final()
        sql = sql.replace("GROUP BY", " AND svl.active = 't' GROUP BY")
        return sql
