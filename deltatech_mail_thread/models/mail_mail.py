# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import threading

from odoo import api, fields, models, tools, registry
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
import odoo.addons.decimal_precision as dp
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    """ Model holding RFC2822 email messages to send. This model also provides
        facilities to queue and send new email messages.  """
    _inherit = 'mail.mail'



    @api.multi
    def _send_in_thread(self, auto_commit=False, raise_exception=False):
        with api.Environment.manage():
            # As this function is in a new thread, i need to open a new cursor, because the old one may be closed
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))

            try:
                super(MailMail, self).send(auto_commit, raise_exception)
            except Exception:
                self._cr.rollback()
                self._cr.close()
                return {}
            self._cr.commit()

            self._cr.close()
            return {}

    @api.multi
    def send(self, auto_commit=False, raise_exception=False):
        threaded_calculation = threading.Thread(target=self._send_in_thread, args=(auto_commit,raise_exception))
        threaded_calculation.start()

        return True

