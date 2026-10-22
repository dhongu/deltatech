# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request


class WarehouseStockConfig(http.Controller):
    @http.route("/website/warehouse_stock/config", type="jsonrpc", auth="user")
    def warehouse_stock_config(self, field, value):
        """Design option of the stock per warehouse, changed from the website editor."""
        if not request.env.user.has_group("website.group_website_designer"):
            raise AccessError(request.env._("Only website designers can change the stock display."))
        request.env["website"].get_current_website()._warehouse_stock_editor_write(field, value)
        return True
