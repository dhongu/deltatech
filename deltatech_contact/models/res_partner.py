# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, RedirectWarning
import odoo.addons.decimal_precision as dp
from odoo.api import Environment
import time


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def check_cnp(self):
        # la import in fisiere sa nu mai faca validarea
        if 'install_mode' in self.env.context:
            return True
        for contact in self:

            if not contact.cnp:
                return True
            cnp = contact.cnp.strip()
            if not cnp:
                return True
            if len(cnp) != 13:
                return False
            key = '279146358279'
            suma = 0
            for i in range(len(key)):
                suma += int(cnp[i]) * int(key[i])

            if suma % 11 == 10:
                rest = 1
            else:
                rest = suma % 11

            if rest == int(cnp[12]):
                return True
            else:
                return False

    cnp = fields.Char(string='CNP', size=13)

    id_nr = fields.Char(string='ID Nr', size=12)
    id_issued_by = fields.Char(string='ID Issued by', size=20)
    mean_transp = fields.Char(string='Mean Transport', size=12)
    is_department = fields.Boolean(string='Is department', compute='_compute_is_department')
    birthdate = fields.Date(string="Birthdate")

    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female'),
                               ('other', 'Other'),
                               ])
    _constraints = [(check_cnp, _("CNP invalid"), ["cnp"]), ]




    @api.onchange('cnp')
    def cnp_change(self):
        if self.cnp and len(self.cnp) > 7:
            birthdate = self.cnp[1:7]
            # Year 2000 (Y2K) issues
            if self.cnp[0] in ['1', '2']:
                birthdate = '19' + birthdate
            else:
                birthdate = '20' + birthdate
            self.birthdate = time.strftime("%Y-%m-%d", time.strptime(birthdate, "%Y%m%d"))
            if self.cnp[0] in ['1', '5']:
                self.gender = 'male'
            else:
                self.gender = 'female'

    @api.onchange('birthdate')
    def birthdate_change(self):
        if self.cnp and self.birthdate:
            cnp = self.cnp
            cnp = cnp[0] + time.strftime("%y%m%d", time.strptime(self.birthdate, "%Y-%m-%d")) + cnp[7:12]
            key = '279146358279'
            suma = 0
            for i in range(len(key)):
                suma += int(cnp[i]) * int(key[i])
            if suma % 11 == 10:
                rest = 1
            else:
                rest = suma % 11
            self.cnp = cnp + str(rest)

    @api.one
    @api.depends('type', 'is_company')
    def _compute_is_department(self):
        if self.is_company or self.type == 'contact':
            self.is_department = False
        else:
            self.is_department = True



    @api.multi
    def name_get(self):
        context = self.env.context

        res = []
        for record in self:
            name = record.name
            if name:
                if record.parent_id and not record.is_company and record.type != 'contact':
                    name = "%s, %s" % (record.parent_name, name)
                if context.get('show_address_only'):
                    name = record._display_address(without_company=True)
                if context.get('show_address'):
                    name = name + "\n" + record._display_address(without_company=True)
                if context.get('show_email') and record.email:
                    name = "%s <%s>" % (name, record.email)
                if context.get('show_phone') and record.phone:
                    name = "%s\n<%s>" % (name, record.phone)
                if context.get('show_category') and record.category_id:
                    cat = []
                    for category in record.category_id:
                        cat.append(category.name)
                    name = name + "\n[" + ','.join(cat) + "]"
                name = name.replace('\n\n', '\n')
                name = name.replace('\n\n', '\n')
                res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        res_vat = []
        if name and len(name) > 2:
            partner_ids = self.search([('vat', 'ilike', name), ('is_company', '=', True)], limit=10)
            if partner_ids:
                res_vat = partner_ids.name_get()
        res = super(res_partner, self).name_search(name, args, operator=operator, limit=limit) + res_vat
        return res

    @api.model
    def create(self, vals):
        if 'cnp' in vals:
            if not self.check_cnp():
                vals['cnp'] = ''
        return super(res_partner, self).create(vals)
