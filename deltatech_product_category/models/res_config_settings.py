# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_share_product_category = fields.Boolean(
        'Share product category to all companies',
        help="Share your product category to all companies defined in your instance.\n"
             " * Checked : Product category are visible for every company, even if a company is defined on the partner.\n"
             " * Unchecked : Each company can see only its product category (product category where company is defined). Product category not related to a company are visible for all companies.")


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        product_rule = self.env.ref('deltatech_product_category.product_category_comp_rule')
        res.update(
            company_share_product=not bool(product_rule.active),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        product_rule = self.env.ref('deltatech_product_category.product_category_comp_rule')
        product_rule.write({'active': not bool(self.company_share_product)})
