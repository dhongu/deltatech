


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
        wizard = self.env['wizard.download.file'].create({'data_file': data_file, 'file_name': 'cash_box_close.inp'})
        # self.write({'data_file': data_file, 'file_name': 'cash_box_in.inp'})

        return wizard.do_download_file()
