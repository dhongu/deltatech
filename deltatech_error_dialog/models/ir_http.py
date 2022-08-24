# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class Http(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super(Http, self).session_info()
        result["support_url"] = "https://www.terrabit.ro/helpdesk"

        return result
