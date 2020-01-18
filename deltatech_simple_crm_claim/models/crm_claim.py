# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
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

import odoo
from odoo import models, fields, api, _
from odoo.tools import html2plaintext


class crm_case_categ(models.Model):
    """ Category of Case """
    _name = "crm.case.categ"
    _description = "Category of Case"

    @api.model
    def _find_object_id(self):
        """Finds id for case object"""
        object_id = self.env.context.get('object_id', False)
        object_name = self.env.context.get('object_name', False)
        object_id = self.env['ir.model'].search(['|', ('id', '=', object_id), ('model', '=', object_name)], limit=1)
        return object_id

    name = fields.Char('Name', required=True, translate=True)
    team_id = fields.Many2one('crm.team', 'Sales Team')
    object_id = fields.Many2one('ir.model', 'Object Name', default=_find_object_id)


class crm_claim_stage(models.Model):
    """ Model for claim stages. This models the main stages of a claim
        management flow. Main CRM objects (leads, opportunities, project
        issues, ...) will now use only stages, instead of state and stages.
        Stages are for example used to display the kanban view of records.
    """
    _name = "crm.claim.stage"
    _description = "Claim stages"
    _rec_name = 'name'
    _order = "sequence"

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', help="Used to order stages. Lower is better.", default=1)
    team_ids = fields.Many2many('crm.team', 'crm_team_claim_stage_rel', 'stage_id', 'team_id', string='Teams',
                                help="Link between stages and sales teams. When set, this limitate the current stage to the selected sales teams.")

    # section_ids = fields.Many2many('crm.team', 'section_claim_stage_rel', 'stage_id', 'section_id',
    #                                string='Sections',
    #                                help="Link between stages and sales teams. When set, this limitate the current stage to the selected sales teams.")
    case_default = fields.Boolean('Common to All Teams',
                                  help="If you check this field, this stage will be proposed by default on each sales team. It will not assign this stage to existing teams.")


class crm_claim(models.Model):
    """ Crm claim
    """
    _name = "crm.claim"
    _description = "Claim"
    _order = "priority,date desc"
    _inherit = ['mail.thread']

    @api.model
    def _get_default_stage_id(self):
        """ Gives default stage_id """
        team_id = self.env['crm.team']._get_default_team_id()
        return self.stage_find([], team_id, [('sequence', '=', '1')])

    @api.model
    def _reference_models(self):
        models = self.env['res.request.link'].search([])
        return [(model.object, model.name) for model in models]

    id = fields.Integer('ID', readonly=True)
    name = fields.Char('Claim Subject', required=True)
    active = fields.Boolean('Active', default=1)
    action_next = fields.Char('Next Action')
    date_action_next = fields.Datetime('Next Action Date')
    description = fields.Text('Description')
    resolution = fields.Text('Resolution')
    create_date = fields.Datetime('Creation Date', readonly=True)
    write_date = fields.Datetime('Update Date', readonly=True)
    date_deadline = fields.Date('Deadline')
    date_closed = fields.Datetime('Closed', readonly=True)
    date = fields.Datetime('Claim Date', index=True, defalut=fields.Datetime.now)

    ref = fields.Char()
    #ref = fields.Reference(string='Reference', selection='_reference_models')
    # ref = fields.Reference(string='Reference', selection=openerp.addons.base.res.res_request.referencable_models)

    categ_id = fields.Many2one('crm.case.categ', 'Category',
                               domain="[('team_id','=',team_id),   ('object_id.model', '=', 'crm.claim')]")
    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')], 'Priority', default='1')
    type_action = fields.Selection([('correction', 'Corrective Action'), ('prevention', 'Preventive Action')],
                                   'Action Type')
    user_id = fields.Many2one('res.users', 'Responsible', track_visibility='always', default=lambda self: self.env.user.id)
    user_fault = fields.Char('Trouble Responsible')
    team_id = fields.Many2one('crm.team', 'Sales Team', \
                              index=True, help="Responsible sales team." \
                                               " Define Responsible user and Email account for" \
                                               " mail gateway.")

    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('crm.case'))
    partner_id = fields.Many2one('res.partner', 'Partner')
    email_cc = fields.Text('Watchers Emails', size=252,
                           help="These email addresses will be added to the CC field of all inbound and outbound emails for this record before being sent. Separate multiple email addresses with a comma")
    email_from = fields.Char('Email', size=128, help="Destination email for email gateway.")
    partner_phone = fields.Char('Phone')
    stage_id = fields.Many2one('crm.claim.stage', 'Stage', track_visibility='onchange', default=_get_default_stage_id,
                               domain="['|', ('team_ids', '=', team_id), ('case_default', '=', True)]")
    cause = fields.Text('Root Cause')

    @api.model
    def stage_find(self, cases, team_id, domain=[], order='sequence'):
        """ Override of the base.stage method
            Parameter of the stage search taken from the lead:
            - team_id: if set, stages must belong to this team or
              be a default case
        """
        if isinstance(cases, (int)):
            cases = self.browse(cases)
        # collect all team_ids
        team_ids = []
        if team_id:
            team_ids.append(team_id.id)
        for claim in cases:
            if claim.team_id:
                team_ids.append(claim.team_id.id)
        # OR all team_ids and OR with case_default
        search_domain = []
        if team_ids:
            search_domain += [('|')] * len(team_ids)
            for team_id in team_ids:
                search_domain.append(('team_ids', '=', team_id))
        search_domain.append(('case_default', '=', True))
        # AND with the domain in parameter
        search_domain += list(domain)
        # perform search, return the first found
        stage_id = self.env['crm.claim.stage'].search(search_domain, order=order, limit=1)
        if stage_id:
            return stage_id.id
        return False

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            return {'value': {'email_from': False, 'partner_phone': False}}
        address = self.partner_id
        return {'value': {'email_from': address.email, 'partner_phone': address.phone}}

    @api.model
    def create(self, vals):
        if vals.get('team_id') and not self.env.context.get('default_team_id'):
            default_team_id = vals.get('team_id')
            self = self.with_context(default_team_id=default_team_id)

        # context: no_log, because subtype already handle this
        return super(crm_claim, self).create(vals)

    @api.multi
    def copy(self, default=None):
        claim = self
        default = dict(default or {}, stage_id=self._get_default_stage_id(), name=_('%s (copy)') % claim.name)
        return super(crm_claim, self).copy(default)

    # -------------------------------------------------------
    # Mail gateway
    # -------------------------------------------------------

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override updates the document according to the email.
        """
        if custom_values is None:
            custom_values = {}
        desc = html2plaintext(msg_dict.get('body')) if msg_dict.get('body') else ''
        defaults = {
            'name': msg_dict.get('subject') or _("No Subject"),
            'description': desc,
            'email_from': msg_dict.get('from'),
            'email_cc': msg_dict.get('cc'),
            'partner_id': msg_dict.get('author_id', False),
        }
        if msg_dict.get('priority'):
            defaults['priority'] = msg_dict.get('priority')
        defaults.update(custom_values)
        return super(crm_claim, self).message_new(msg_dict, custom_values=defaults)


class res_partner(models.Model):
    _inherit = 'res.partner'

    claim_count = fields.Integer(string='# Claims', compute='_compute_claim_count')

    @api.multi
    def _compute_claim_count(self):
        for partner in self:
            partner.claim_count = self.env['crm.claim'].search_count([('partner_id', '=', partner.id)])

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
