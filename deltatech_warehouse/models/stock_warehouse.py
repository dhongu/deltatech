# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    pick_type_prod_consume_id = fields.Many2one(
        "stock.picking.type", string="Type prod consume", help="Picking type consume in production"
    )
    pick_type_prod_receipt_id = fields.Many2one(
        "stock.picking.type", string="Type prod receipt", help="Picking type receipt from production"
    )
