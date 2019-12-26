# -*- coding: utf-8 -*-
# ©  2019 Deltatech
# See README.rst file on addons root folder for license details

from os import path
import base64
import zipfile
from io import StringIO
from io import BytesIO

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError
import odoo.addons.decimal_precision as dp

import html2text
import odoo.addons.decimal_precision as dp


class export_attachment(models.TransientModel):
    _name = 'export.attachment'
    _description = "Export attachment"

    name = fields.Char(string='File Name', readonly=True)
    data_file = fields.Binary(string='File', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    domain = fields.Char(default='[]')

    @api.multi
    def do_export(self):
        buff = BytesIO()

        files = []

        # This is my zip file
        zip_archive = zipfile.ZipFile(buff, mode='w')



        domain = eval(self.domain)
        attachments = self.env['ir.attachment'].search(domain)
        for attachment in attachments:
            if attachment.store_fname:
                full_path = attachment._full_path(str(attachment.store_fname))
                if path.exists(full_path):
                    # file = open(full_path,'rb').read()
                    file_name = attachment.store_fname
                    zip_archive.write(full_path, file_name)

        # Here you finish editing your zip. Now all the information is
        # in your buff StringIO object
        zip_archive.close()
        out = base64.encodebytes(buff.getvalue())
        buff.close()

        filename = 'ExportOdooAttachment'
        extension = 'zip'

        name = "%s.%s" % (filename, extension)
        self.write({'state': 'get', 'data_file': out, 'name': name, })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'export.attachment',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
