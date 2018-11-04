# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

from . import registry_office_common


class RegistryOfficDoc(models.Model):
    _name = 'registry.office.doc'
    _description = "Document"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    category = fields.Selection([('E', 'Entry document'), ('O', 'Output document'), ('I', 'Internal document')],
                                readonly=True, states={'new': [('readonly', False)]},
                                default='E', string='Category')
    sender_id = fields.Many2one('res.partner', string="Sender", required=True,
                                readonly=True, states={'new': [('readonly', False)]},
                                index=True)  # Provenienta
    recipient_id = fields.Many2one('res.partner', string="Recipient",
                                   readonly=True, states={'new': [('readonly', False)]},
                                   track_visibility='always',
                                   index=True)  # Destinatar

    cnp = fields.Char(related="sender_id.cnp", readonly=True, states={'new': [('readonly', False)]}, )
    vat = fields.Char(related="sender_id.vat", readonly=True, states={'new': [('readonly', False)]}, )

    # Numar, data actului
    external_number = fields.Char("External Number", readonly=True, states={'new': [('readonly', False)]}, )
    external_date = fields.Date("External Date", readonly=True, states={'new': [('readonly', False)]}, )

    name = fields.Char("Number", index=True, readonly=True, states={'new': [('readonly', False)]}, required=True,
                       default='/')

    date = fields.Date(readonly=True, states={'new': [('readonly', False)]}, required=True, default=fields.Date.today)

    is_company = fields.Boolean(related="sender_id.is_company", readonly=True, states={'new': [('readonly', False)]})
    city = fields.Char(related="sender_id.city", readonly=True, states={'new': [('readonly', False)]})
    street = fields.Char(related="sender_id.street", readonly=True, states={'new': [('readonly', False)]})
    street2 = fields.Char(related="sender_id.street2", readonly=True, states={'new': [('readonly', False)]})
    state_id = fields.Many2one("res.country.state", related="sender_id.state_id", readonly=True,
                               states={'new': [('readonly', False)]})
    zip = fields.Char(related="sender_id.zip", readonly=True, states={'new': [('readonly', False)]})
    country_id = fields.Many2one('res.country', related="sender_id.country_id", readonly=True,
                                 states={'new': [('readonly', False)]})
    phone = fields.Char(related="sender_id.phone", readonly=True, states={'new': [('readonly', False)]})
    email = fields.Char(related="sender_id.email", readonly=True, states={'new': [('readonly', False)]})

    type_id = fields.Many2one("registry.office.doc_type", readonly=True, states={'new': [('readonly', False)]},
                              required=True, )  # Tip de act
    description = fields.Text(readonly=True, states={'new': [('readonly', False)]}, )  # Cuprinsul actului
    note = fields.Text(readonly=True, states={'new': [('readonly', False)]}, )  # observatii

    related_doc_id = fields.Many2one('registry.office.doc', readonly=True,
                                     states={'new': [('readonly', False)]}, )  # o	Conex cu numarul

    doc_ids = fields.One2many('registry.office.doc', 'related_doc_id', readonly=True)

    solution_deadline = fields.Integer(default=30, readonly=True,
                                       states={'new': [('readonly', False)]}, )  # Termen de rezolvare
    tabs_number = fields.Integer(default=1, readonly=True, states={'new': [('readonly', False)]}, )  # Numarul de file
    folder_id = fields.Many2one('registry.office.folder')  # Dosar

    shipment_date = fields.Date(string='Date of shipment')  # data expediere
    shipment_pertner_id = fields.Many2one('res.partner', string="Shipped by")  # expediata de
    shipment_note = fields.Char('Shipment Note')
    shipment_id = fields.Many2one('registry.office.shipment')

    is_send = fields.Boolean()  # expediat
    state = fields.Selection(registry_office_common.selection_state,
                             default='new', string='Status', track_visibility='always')

    user_id = fields.Many2one('res.users', string='Responsible', readonly=True, states={'new': [('readonly', False)]})
    date_assign = fields.Datetime('Date Assigning', readonly=True, copy=False)
    date_start = fields.Datetime('Start Date', readonly=True, copy=False)
    date_done = fields.Datetime('Done Date', readonly=True, copy=False)

    attachment_ids = fields.One2many('ir.attachment', compute='_compute_attachment_ids', string="Attachments")
    attachment_count = fields.Integer(compute='_compute_attachment_ids', string="Attachments count")

    @api.onchange('recipient_id')
    def onchange_recipient_id(self):
        if self.recipient_id:
            self.user_id = self.get_user_for_partner(self.recipient_id)

    @api.multi
    def _compute_attachment_ids(self):

        attachments = self.env['ir.attachment'].search(
            [('res_model', '=', 'registry.office.doc'), ('res_id', 'in', self.ids)])
        result = dict.fromkeys(self.ids, self.env['ir.attachment'])
        for attachment in attachments:
            result[attachment.res_id] |= attachment

        for doc in self:
            doc.attachment_ids = result[doc.id]
            # for child in doc.doc_ids:
            #     doc.attachment_ids |= child.attachment_ids
            doc.attachment_count = len(doc.attachment_ids)

    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('id', 'in', self.attachment_ids.ids)]
        res['context'] = {
            'default_res_model': 'registry.office.doc',
            'default_res_id': self.id,
            'create': False,
            'edit': False,
        }
        return res

    @api.onchange('type_id')
    def onchange_type_id(self):
        if self.type_id:
            self.solution_deadline = self.type_id.solution_deadline

    def set_user(self, vals):
        if not 'user_id' in vals:
            if 'recipient_id' in vals and vals['recipient_id']:
                vals['state'] = 'assigned'
                vals['date_assign'] = fields.Datetime.now()
                user = self.get_user_for_partner(vals['recipient_id'])
                if user:
                    vals['user_id'] = user.id
        return vals

    @api.model
    def create(self, vals):
        if vals['name'] == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('doc.number')

        vals = self.set_user(vals)
        return super(RegistryOfficDoc, self).create(vals)

    @api.multi
    def write(self, vals):

        vals = self.set_user(vals)
        return super(RegistryOfficDoc, self).write(vals)

    def get_user_for_partner(self, partner):
        if isinstance(partner, int):
            partner = self.env['res.partner'].browse(partner)
        user = self.env['res.users'].search([('partner_id', '=', partner.id)], limit=1)
        if not user:
            user = self.env['res.users'].search([('partner_id', 'in', partner.child_ids)], limit=1)
        return user

    @api.multi
    def action_taking(self):
        if self.state != 'new':
            raise Warning(_('Documents is already assigned.'))
        # self.message_mark_as_read()
        self.write({'state': 'assigned',
                    'date_assign': fields.Datetime.now(),
                    'user_id': self.env.user.id})

    @api.multi
    def action_start(self):
        for doc in self:
            if not doc.user_id and doc.state == 'new':
                doc.action_taking()
            if doc.state not in ['assigned']:
                raise Warning(_('The document is not assigned.'))
            if doc.user_id and doc.user_id != self.env.user:
                raise Warning(_('The document is assigned to the % user') % doc.user_id.name)

        self.write({
            'state': 'progress',
            'user_id': self.env.user.id,
            'date_start': fields.Datetime.now()
        })

    @api.multi
    def action_assing(self):  # transfer!
        if not self.user_id:
            raise Warning(_('Please select a responsible.'))
        if self.state != 'new':
            raise Warning(_('Documents is already assigned.'))

        self.write({'state': 'assigned',
                    'date_assign': fields.Datetime.now()})

        new_follower_ids = [self.user_id.partner_id.id]

        if self.user_id != self.env.user:
            msg = _('Please solve the document %s: %s') % (self.name, self.date)

            if msg and not self.env.context.get('no_message', False):
                document = self
                message = self.env['mail.message'].with_context({'default_starred': True}).create({
                    'model': 'registry.office.doc',
                    'res_id': document.id,
                    'record_name': document.name_get()[0][1],
                    'email_from': self.env['mail.message']._get_default_from(),
                    'reply_to': self.env['mail.message']._get_default_from(),

                    'subject': self.subject,
                    'body': msg,

                    'message_id': self.env['mail.message']._get_message_id({'no_auto_thread': True}),
                    'partner_ids': [(4, id) for id in new_follower_ids],

                })

    @api.multi
    def action_done(self):
        self.write({'state': 'done',
                    'date_done': fields.Datetime.now()})

        new_follower_ids = []
        if self.category == 'I':
            new_follower_ids = [self.sender_id.id]
        if self.category == 'O':
            new_follower_ids = [self.recipient_id.id]

        if self.user_id != self.env.user.id:
            msg = _('Document %s  %s was done') % (self.name, self.date)

            if msg and not self.env.context.get('no_message', False):
                document = self
                message = self.env['mail.message'].with_context({'default_starred': True}).create({
                    'model': 'registry.office.doc',
                    'res_id': document.id,
                    'record_name': document.name_get()[0][1],
                    'email_from': self.env['mail.message']._get_default_from(),
                    'reply_to': self.env['mail.message']._get_default_from(),

                    'subject': self.subject,
                    'body': msg,

                    'message_id': self.env['mail.message']._get_message_id({'no_auto_thread': True}),
                    'partner_ids': [(4, id) for id in new_follower_ids],

                })

    @api.multi
    def action_receipt(self):
        pass

    @api.multi
    def action_barcode(self):
        pass


class RegistryOfficHistory(models.Model):
    _name = 'registry.office.history'
    _description = "Document"

    date_in = fields.Datetime('Date input')  # data si ora cand a venit documentul
    date_out = fields.Datetime('Date output')  # data si ora cand a fost trimis documentul
    doc_id = fields.Many2one('registry.office.doc')
    state = fields.Selection(registry_office_common.selection_state,
                             default='new', string='Status', track_visibility='always')

    shipment_pertner_id = fields.Many2one('res.partner', string="Shipped by")  # expediata de
    shipment_note = fields.Char('Shipment Note')
    shipment_id = fields.Many2one('registry.office.shipment')
