# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Terrabit All Rights Reserved


from openerp import models, fields, api, _


class resource_replace_rule(models.Model):
    _name = 'resource.replace.rule'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', help="Determine the display order")
    parent_id = fields.Many2one('product.template', string='Article')
    from_product = fields.Many2one('product.product', string='Original Product')
    to_product = fields.Many2one('product.product', string='New Product')
    factor = fields.Float(string='Factor', default=1.0)
    type = fields.Selection([('Replace','Replace'),('Add','Add'), ('Replace master','Replace master')], default='Replace')

class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def button_convert_sale(self):
        # get all rules
        rules = self.env['resource.replace.rule'].search([])
        for order in self:
            new_sale = order.copy()
            articles = new_sale.article_ids
            for article in articles:
                for rule in rules:
                    if rule.parent_id == article.product_template:
                        if rule.type == 'Replace':
                            for resource in article.resource_ids:
                                if resource.product_id == rule.from_product:
                                    new_qty = resource.product_uom_qty*rule.factor
                                    resource.product_id = rule.to_product
                                    resource.product_uom_qty = new_qty
                                    resource.name = rule.to_product.display_name
                                    # modificare pret resursa
                                    price = order.pricelist_id.price_get(resource.product_id.id,
                                                                         resource.product_uom_qty or 1.0,
                                                                         order.partner_id.id)[order.pricelist_id.id]
                                    price = self.env['product.uom']._compute_price(resource.product_id.uom_id.id, price,
                                                                                   resource.product_uom.id)

                                    from_currency = self.env.user.company_id.currency_id.with_context(
                                        date=order.date_order)

                                    purchase_price = from_currency.compute(
                                        resource.product_id.standard_price or self.product_id.product_tmpl_id.standard_price,
                                        order.pricelist_id.currency_id)

                                    amount = resource.product_uom_qty * resource.price_unit

                                    resource.write(
                                        {'price_unit': price, 'purchase_price': purchase_price, 'amount': amount})
                                    # modificare atribute in article
                                    for attribute in article.product_attributes:
                                        for attr_new_value in rule.to_product.attribute_value_ids:
                                            if attribute.attribute == attr_new_value.attribute_id:
                                                attribute.value = attr_new_value
                        else: #vedem cum facem in alte cazuri
                            if rule.type == 'Replace master':
                                if rule.from_product == article.product_id:
                                    new_template = rule.to_product.product_tmpl_id
                                    article.write({
                                        'product_template': new_template.id,
                                        'product_id': rule.to_product.id,
                                    })
                                    article.onchange_product_template()
                article._compute_amount()
                # do not explode, resets quantities
                # article.explode_bom()
            return {
                'res_id': new_sale.id,
                'domain': "[('id','=', " + str(new_sale.id) + ")]",
                'name': _(''),
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'sale.order',
                'view_id': False,
                'target': 'current',
                'nodestroy': True,
                'type': 'ir.actions.act_window'
            }


