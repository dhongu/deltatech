# -*- coding: utf-8 -*-
# ©  2019 Terrabit
# See README.rst file on addons root folder for license details


from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, UserError


class ProductProduct(models.Model):
    _inherit = "product.product"

    def create_rule(self):
        warehouse_id = self.env['ir.config_parameter'].sudo().get_param('deltatech_product_auto_rule.default_rule_warehouse_id')
        warehouse = self.env['stock.warehouse'].sudo().search([('id','=',warehouse_id)])
        if not warehouse:
            raise UserError(_('Default warehouse ID not set or not exists! Check config parameters'))

        location_id = self.env['ir.config_parameter'].sudo().get_param('deltatech_product_auto_rule.default_rule_location_id')
        location = self.env['stock.location'].sudo().search([('id', '=', location_id)])
        if not location:
            raise UserError(_('Default location ID not set or not exists! Check config parameters'))

        for record in self:
            rules = record.env['stock.warehouse.orderpoint'].search([('product_id','=',record.id)])
            if not rules:
                new_rule = record.env['stock.warehouse.orderpoint'].create({
                    'warehouse_id':warehouse_id,
                    'location_id':location_id,
                    'product_id':record.id,
                    'product_min_qty':0,
                    'product_max_qty':0,
                    'lead_days': 0
                })

    @api.model
    def create(self, vals):
        warehouse_id = self.env['ir.config_parameter'].sudo().get_param('deltatech_product_auto_rule.default_rule_warehouse_id')
        warehouse = self.env['stock.warehouse'].sudo().search([('id', '=', warehouse_id)])
        if not warehouse:
            warehouse_id = False

        location_id = self.env['ir.config_parameter'].sudo().get_param('deltatech_product_auto_rule.default_rule_location_id')
        location = self.env['stock.location'].sudo().search([('id', '=', location_id)])
        if not location:
            location_id = False
        prod_id = super(ProductProduct, self).create(vals)
        new_rule = self.env['stock.warehouse.orderpoint'].create({
            'warehouse_id': warehouse_id,
            'location_id': location_id,
            'product_id': prod_id.id,
            'product_min_qty': 0,
            'product_max_qty': 0,
            'lead_days':0
        })
        return prod_id