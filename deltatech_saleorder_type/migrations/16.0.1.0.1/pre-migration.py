

import logging
from  odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("_____________ Migration pre-script  _____________")


    util.fields.rename_field(cr, 'sale.order', 'so_type', 'sale_order_type')
