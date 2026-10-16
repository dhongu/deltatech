# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = "website"

    def _get_product_sort_mapping(self):
        # in 20.0 the standard mapping is the (tuple) selection of shop_default_sort
        sort_mapping = list(super()._get_product_sort_mapping())

        sort_mapping += [
            ("sales_count2 desc", self.env._("Best sellers")),
            ("visit_count desc", self.env._("Most Visited")),
            ("rating_count2 desc", self.env._("Reviews")),
            ("rating_avg2 desc", self.env._("Best Review")),
            ("in_stock desc", self.env._("Availability")),
        ]

        return tuple(sort_mapping)
