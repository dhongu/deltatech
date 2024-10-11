# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

import logging

from odoo import _, api, models

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def create_missing_orderpoint(self):
        sql = """
            SELECT pp.id, pp.default_code
            FROM product_product pp
            LEFT JOIN stock_warehouse_orderpoint swo ON pp.id = swo.product_id
            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
            WHERE swo.product_id IS NULL AND pt.detailed_type = 'product';
        """
        self.env.cr.execute(sql)
        product_ids = [x[0] for x in self.env.cr.fetchall()]
        products = self.browse(product_ids)
        products.create_rule()
        _logger.info(_("Created %s missing rules" % len(product_ids)))
