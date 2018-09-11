# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, tools, _
from odoo.exceptions import except_orm, Warning, RedirectWarning


class account_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    """ In 11 nu exista metoda, trebuie sa adaug un boton sa ceva"""

    @api.multi
    def set_product_taxes(self):
        config = self
        # config.default_sale_tax  self.default_sale_tax_id:
        # config.default_purchase_tax self.default_purchase_tax_id:
        print ("setez noile cote de TVA")
        products = self.env['product.template'].search([])
        print ("Nr prod", len(products))
        products.write({
            'taxes_id': [(6, 0, [config.default_sale_tax_id.id])],
            'supplier_taxes_id': [(6, 0, [config.default_purchase_tax_id.id])]
        })

    @api.multi
    def set_sale_order_taxes(self):
        config = self
        # de recalculat totalul din comenzile de vanzare
        # comenzi de vanzare deschise
        order_lines = self.env['sale.order.line'].search([('state', 'not in', ['done', 'cancel'])])
        print (" Linii de comenzi de vanzare", len(order_lines))
        order_lines.write({'tax_id': [(6, 0, [config.default_sale_tax_id.id])]})

    @api.multi
    def set_sale_order_taxes(self):
        config = self
        # de recalculat totalul din comenzile de achizitie
        # comenzi de achizitie deschise
        order_lines = self.env['purchase.order.line'].search([('state', 'not in', ['done', 'cancel'])])
        print (" Linii de comenzi de achizitie", len(order_lines))
        order_lines.write({'taxes_id': [(6, 0, [config.default_purchase_tax_id.id])]})
