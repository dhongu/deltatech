# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.http import request


class website(models.Model):
    _inherit = 'website'
 
    @api.multi
    def sale_product_domain(self):
        domain = super(website,self).sale_product_domain()
        search = request.params.get('search',False)
        if search:
            product_ids = []
            alt_domain = []
            for srch in search.split(" "):
                alt_domain += [ ('name', 'ilike', srch)]
            alternative_ids =  self.env['product.alternative'].search(  alt_domain, limit=10 ) 
            for alternative in alternative_ids:
                product_ids += [alternative.product_tmpl_id.id]
            if product_ids:
                if len(product_ids)==1:
                    domain += ['|',('id','=', product_ids[0])]
                else:
                    domain += ['|',('id','in', product_ids)]
                         
        return domain


    # def _image(self, cr, uid, model, id, field, response, max_width=maxint, max_height=maxint, cache=None, context=None):
    #
    #     if model == 'product.template' and field == 'image':
    #         field = 'watermark_image'
    #
    #     response =  super(website,self)._image(cr, uid, model, id, field, response, max_width, max_height, cache, context)
    #     return response

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def binary_content(cls, xmlid=None, model='ir.attachment', id=None, field='datas',
                       unique=False, filename=None, filename_field='datas_fname', download=False,
                       mimetype=None, default_mimetype='application/octet-stream',
                       access_token=None, related_id=None, access_mode=None, env=None):

        if model == 'product.template' and field == 'image':
            field = 'watermark_image'

        return super(IrHttp, cls).binary_content(
            xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename,
            filename_field=filename_field, download=download, mimetype=mimetype,
            default_mimetype=default_mimetype, access_token=access_token, related_id=related_id,
            access_mode=access_mode, env=env)
