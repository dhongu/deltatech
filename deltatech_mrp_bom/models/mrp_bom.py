# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _




class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    _rec_name = "name"

    name = fields.Char(string="Name")


    @api.onchange('product_id')
    def onchange_product_id(self):
        super(MrpBomLine, self).onchange_product_id()
        if self.product_id:
            self.name = self.product_id.name

    @api.model
    def create(self, vals):
        if 'name' not in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals['name'] = product.name
        return super(MrpBomLine,self).create(vals)

    @api.multi
    def open_bom(self):
        self.ensure_one()
        if self.child_bom_id:
            # print "Deschid sublista de materiale"
            return {
                'res_id': self.child_bom_id.id,
                'domain': "[('id','=', " + str(self.child_bom_id.id) + ")]",
                'name': _('BOM'),
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'mrp.bom',
                'view_id': False,
                'target': 'current',
                'nodestroy': True,
                'type': 'ir.actions.act_window'
            }

    @api.model_cr
    def init(self):
        super(MrpBomLine, self).init()
        lines = self.search([('name', '=', False)])
        for line in lines:
            line.write({'name': line.product_id.name})
