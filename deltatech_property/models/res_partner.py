# coding=utf-8
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import datetime
from odoo.modules import get_module_resource

class Partner(models.Model):
    _inherit = "res.partner"

    type = fields.Selection(selection_add=[('land','Land'),
                                           ('building','Building')])





    @api.model
    def _get_default_image(self, partner_type, is_company, parent_id):

        if partner_type not in ['land','building']:
            return super(Partner, self)._get_default_image(partner_type, is_company, parent_id)


        if partner_type == 'land':
            img_path = get_module_resource('deltatech_property', 'static/src/img', 'land.png')
        else:
            img_path = get_module_resource('deltatech_property', 'static/src/img', 'building.png')

        with open(img_path, 'rb') as f:
            image = f.read()

        image = tools.image_colorize(image)

        return tools.image_resize_image_big(image.encode('base64'))