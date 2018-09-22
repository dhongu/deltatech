# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

import base64



class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_pos_session_validate(self):
        super(PosSession, self).action_pos_session_validate()
        data_file = 'Z,1,______,_,__;;;;;;;'
        data_file = base64.encodestring(data_file.encode())
        ext =  self.config_id.file_ext
        name = self.name.replace('/','_')
        file_name = 'cash_box_%s_close.%s' % (name, ext)
        wizard = self.env['wizard.download.file'].create({'data_file': data_file, 'file_name':file_name })
        # self.write({'data_file': data_file, 'file_name': 'cash_box_in.inp'})

        return wizard.do_download_file()
