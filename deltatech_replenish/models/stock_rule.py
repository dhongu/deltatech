# ©  2008-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _make_po_select_supplier(self, values, suppliers):
        """Method intended to be overridden by customized modules to implement any logic in the
        selection of supplier.
        """
        supplier_id = values.get("supplier_id", False)
        if supplier_id:
            return supplier_id
        return suppliers[0]
