# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2014 Deltatech All Rights Reserved
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

# https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/


from odoo import api, fields, models, _
import time
import threading
import sys
import trace


def get_var_by_id(id_val):
    for x in globals().values():
        if id(x) == id_val:
            return x
    return


class background_job(models.Model):
    _name = 'background.job'
    _description = "Background job"

    name = fields.Char(string="Job name")
    start_time = fields.Datetime(string="Start time")
    end_time = fields.Datetime(string="End time")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('pause', 'Pause'),
        ('exception', 'Exception'),
        ('finalized', 'Finalized'),
    ], string='Status', index=True, readonly=True, default='draft')
    thread_address = fields.Char(readonly=True, )

    def _dummy_run(self):
        while True:
            time.sleep(5)

    @api.multi
    def action_start(self):
        values = {'state': 'running', 'start_time': fields.Datetime.now()}
        job_threaded = threading.Thread(target=self._dummy_run)
        if self.name:
            job_threaded.setName(self.name)
        else:
            values['name'] = job_threaded.name
        job_threaded.start()
        values['thread_address'] = id(job_threaded)
        self.write(values)
        return True

    @api.multi
    def action_get(self):
        for thread in threading.enumerate():
            print (thread.name, id(thread), thread)

    @api.multi
    def action_stop(self):
        job_threaded = get_var_by_id(self.thread_address)
        for job in self:
            for thread in threading.enumerate():
                print (thread.name, id(thread), thread)
                if thread.name == job.name:
                    print ("Join")
                    thread.join(0.05)

        self.write({'state': 'finalized', 'end_time': fields.Datetime.now()})

        return True

    @api.multi
    def action_pause(self):
        self.write({'state': 'pause'})
        return True

    @api.multi
    def action_resume(self):
        self.write({'state': 'running'})
        return True

    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
