# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api


class product_category(models.Model):
    _inherit = 'product.category'

    sequence_id = fields.Many2one('ir.sequence', string='Code Sequence')


class product_template(models.Model):
    _inherit = 'product.template'

    #default_code = fields.Char(required=True)  # nu trebuie sa fie obligatori pentru a se putea genera cod dupa creare

    _sql_constraints = [
        ('name_code', 'unique (default_code,active,company_id)', "Internal Reference already exists !"),
    ]


    @api.multi
    def button_new_code(self):
        for product in self:
            if product.default_code in [False, '/', 'auto'] or self.env.context.get('force_code', False):
                if product.categ_id.sequence_id:
                    default_code = product.categ_id.sequence_id.next_by_id()
                    vals = {'default_code': default_code}
                    if product.default_code:
                        vals['alternative_ids'] = [(0, False, {'name': product.default_code})]
                    product.write(vals)

        action = self.env.ref('deltatech_product_code.action_force_new_code')
        action.sudo().unlink_action()

    def force_new_code(self):
        self.with_context(force_code=True).button_new_code()


    @api.model
    def show_not_unique(self):
        sql = '''
             SELECT id FROM
              (SELECT *, count(*) 
                   OVER   (PARTITION BY  default_code, active) AS count
                    FROM product_template) 
               tableWithCount
              WHERE tableWithCount.count > 1;
        '''
        self.env.cr.execute(sql)
        product_ids = [x[0] for x in self.env.cr.fetchall()]

        action = self.env.ref('deltatech_product_code.action_force_new_code')
        action.create_action()

        action = self.env.ref('product.product_template_action').read()[0]

        action['domain'] = [('id', 'in', product_ids)]
        return action


class product_product(models.Model):
    _inherit = 'product.product'

    @api.multi
    def button_new_code(self):
        for product in self:
            if product.default_code in [False, '/', 'auto'] or self.env.context.get('force_code', False):
                if product.categ_id.sequence_id:
                    default_code = product.categ_id.sequence_id.next_by_id()
                    if product.default_code:
                        vals['alternative_ids'] = [(0, False, {'name': product.default_code})]
                    vals = {'default_code': default_code}
                    product.write(vals)
