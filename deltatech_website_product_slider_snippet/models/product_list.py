# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import json
from odoo import fields, models
from odoo.tools.safe_eval import safe_eval



class ProductList(models.Model):
    _inherit = "product.list"

    def get_domain_json(self):

        self.ensure_one()
        domain = safe_eval(self.products_domain)
        return json.dumps(domain)
