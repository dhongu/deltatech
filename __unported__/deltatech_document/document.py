# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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


from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp


class document_file(models.Model):
    _inherit = 'ir.attachment'

    """
    Doc. No: nr document automat dat de sistem.
    Description – camp editabil
    Turtle reference – camp editabil
    Document type – Procedure, Template, Work Instruction
    Departement – camp editabil
    Reasons  – camp editabil
    Issued by: automat numele celui care creaza doc, numai administratorul poate avea acces de editare (asta daca vrea sa emite un doc in numele altei persoane)
    Inform:  – in acest camp sa se poata selecta mai multi utilizatori care vor fi informati de noul document, revizie sau alte modificari.
    Approved by : sa se poat selecta cel putin 1 utilizator care trebuie sa aprobe
     
    Documentul se inregistreaza in arhiva numai dupa ce a fost aprobat.
    Documentele in stand by le pot vedea doar emitentii si cei care trb sa aprobe.
    
    """

    state = fields.Selection([('draft', 'Draft'), ('valid', 'Valid'), ('to_approved', 'To Be Approved'),
                              ('approved', 'Approved'), ('obsoleted', 'Obsoleted')], default="valid")
    categ_id = fields.Many2one('document.category', string="Category", readonly=True,
                               states={'draft': [('readonly', False)]})
    number = fields.Char(string="Number", copy=False, readonly=True)
    ref_turtle = fields.Char(string='Turtle reference', readonly=True, states={'draft': [('readonly', False)]})
    reasons = fields.Char(string="Reasons", readonly=True, states={'draft': [('readonly', False)]})

    to_be_approved_by = fields.Many2many('res.users', 'document_to_be_approved_by', 'document_id', 'user_id', string='To Be Approved by',
                                         copy=False, readonly=True, states={'draft': [('readonly', False)]})
    approved_by = fields.Many2many('res.users', 'document_approved_by', 'document_id',
                                   'user_id', string='Approved by', copy=False, readonly=True)

    replaced_by = fields.Many2one('ir.attachment', string='Replaced By')

    @api.multi
    def set_draft(self):
        for doc in self:
            if doc.state == 'valid':
                doc.write({'state': 'draft'})

    @api.multi
    def set_to_approved(self):
        for doc in self:
            if doc.state == 'draft':
                doc.write({'state': 'to_approved'})

    @api.multi
    def set_doc_number(self):
        self.ensure_one()
        if self.number or not self.categ_id:
            return
        if self.categ_id.sequence_id:
            number = self.categ_id.sequence_id.next_by_id()
            self.write({'number': number})

    @api.multi
    def approve(self):
        for doc in self:
            for ap in doc.to_be_approved_by:
                if ap.id == self.env.user.id:
                    doc.write({'to_be_approved_by': [(2, self.env.user.id, False)],
                               'approved_by': [(4, self.env.user.id, False)]})
                    if not doc.to_be_approved_by:
                        doc.write({'state': 'approved'})
                    # exista o versiune anterioara ? daca da atunci ea trebuie sa treaca in starea  obsoleted

    @api.multi
    def new_version(self):
        self.ensure_one()
        new_doc = self.copy({'state': 'draft'})
        self.replaced_by = new_doc


class docuemt_category(models.Model):
    _name = 'document.category'
    _description = 'Document category'
    _order = 'name'

    name = fields.Char(string='Name')
    sequence_id = fields.Many2one('ir.sequence', string='Documents Sequence')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
