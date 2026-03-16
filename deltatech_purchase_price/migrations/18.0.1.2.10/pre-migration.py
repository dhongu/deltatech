# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.upgrade import util


def migrate(cr, version):
    util.rename_field(cr, "product.product", "last_purchase_price", "last_purchase_price_old_tmp")
    util.rename_field(cr, "product.template", "last_purchase_price", "last_purchase_price_tmpl_old_tmp")
