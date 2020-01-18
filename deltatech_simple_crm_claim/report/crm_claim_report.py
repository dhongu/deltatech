# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from odoo import models, fields, api, _
from odoo import tools

AVAILABLE_PRIORITIES = [
   ('0', 'Low'),
   ('1', 'Normal'),
   ('2', 'High')
]


class crm_claim_report(models.Model):
    """ CRM Claim Report"""

    _name = "crm.claim.report"
    _auto = False
    _description = "CRM Claim Report"


    user_id = fields.Many2one('res.users', 'User', readonly=True)
    team_id  =fields.Many2one('crm.team', 'Section', readonly=True)
    nbr = fields.Integer('# of Claims', readonly=True)  # TDE FIXME master: rename into nbr_claims
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    create_date = fields.Datetime('Create Date', readonly=True, index=True)
    claim_date = fields.Datetime('Claim Date', readonly=True)
    delay_close = fields.Float('Delay to close', digits=(16,2),readonly=True, group_operator="avg",help="Number of Days to close the case")
    stage_id = fields.Many2one ('crm.claim.stage', 'Stage', readonly=True,domain="[('team_ids','=',team_id)]")
    categ_id = fields.Many2one('crm.case.categ', 'Category',\
                         domain="[('team_id','=',team_id),\
                        ('object_id.model', '=', 'crm.claim')]", readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)

    priority = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
    type_action = fields.Selection([('correction','Corrective Action'),('prevention','Preventive Action')], 'Action Type')
    date_closed = fields.Datetime('Close Date', readonly=True, index=True)
    date_deadline = fields.Date('Deadline', readonly=True, index=True)
    delay_expected = fields.Float('Overpassed Deadline',digits=(16,2),readonly=True, group_operator="avg")
    email = fields.Integer('# Emails', size=128, readonly=True)
    subject = fields.Char('Claim Subject', readonly=True)

    @api.model_cr
    def init(self):

        """ Display Number of cases And Section Name
        @param cr: the current row, from the database cursor,
         """

        tools.drop_view_if_exists(self.env.cr, 'crm_claim_report')
        self.env.cr.execute("""
            create or replace view crm_claim_report as (
                select
                    min(c.id) as id,
                    c.date as claim_date,
                    c.date_closed as date_closed,
                    c.date_deadline as date_deadline,
                    c.user_id,
                    c.stage_id,
                    c.team_id,
                    c.partner_id,
                    c.company_id,
                    c.categ_id,
                    c.name as subject,
                    count(*) as nbr,
                    c.priority as priority,
                    c.type_action as type_action,
                    c.create_date as create_date,
                    avg(extract('epoch' from (c.date_closed-c.create_date)))/(3600*24) as  delay_close,
                    (SELECT count(id) FROM mail_message WHERE model='crm.claim' AND res_id=c.id) AS email,
                    extract('epoch' from (c.date_deadline - c.date_closed))/(3600*24) as  delay_expected
                from
                    crm_claim c
                group by c.date,
                        c.user_id,c.team_id, c.stage_id,
                        c.categ_id,c.partner_id,c.company_id,c.create_date,
                        c.priority,c.type_action,c.date_deadline,c.date_closed,c.id
            )""")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
