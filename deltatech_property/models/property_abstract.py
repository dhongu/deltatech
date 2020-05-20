# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, tools, fields, api, _
from datetime import datetime


class PropertyProperty(models.AbstractModel):
    _name = 'property.property'
    _description = "Property"
    _inherits = {'maintenance.equipment': 'base_equipment_id'}

    _inherit =  ['mail.thread', 'mail.activity.mixin']

    # def _default_company(self):
    #     return self.env['res.company']._company_default_get(self._name)

    base_equipment_id = fields.Many2one('maintenance.equipment')

    # exista deja in echipament
    #name = fields.Char(string="Name")


    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')

    #exista deja in
    # company_id = fields.Many2one('res.company', 'Company', index=True, default=_default_company)
    # active = fields.Boolean(default=True)

    owner_id = fields.Many2one('res.partner', string="Owner")

    region_id = fields.Many2one('property.region', string="Region")
    asset_number = fields.Char(string="Asset Number", index=True)

    type_prop = fields.Selection([('patrimony', 'Patrimony'), ('rent', 'Rent'),
                                  ('loan', 'Loan'), ('concession', 'Concession')], string="Property Type")

    class_number = fields.Char(string="Class")
    class_code = fields.Char(string="Classification code")
    cost_center_id = fields.Many2one('property.cost.center', string='Cost Center')
    order_number = fields.Char(string='Order Number')

    acquisition_mode_id = fields.Many2one('property.acquisition', string="Acquisition Mode")
    date_acquisition = fields.Date(string="Acquisition Date")
    doc_acquisition = fields.Char(string="Acquisition Document")

    surface = fields.Float(string="Surface")

    # exista in echipament
    #note = fields.Text()

    doc_count = fields.Integer(string="Number of documents", compute='_get_attached_docs')


    image = fields.Binary(        "Image", attachment=True,
        help="This field holds the image used as image for the property, limited to 1024x1024px.")




    @api.multi
    def _get_attached_docs(self):
        for record in self:
            domain = [('res_model', '=', self._name), ('res_id', '=', record.id)]
            record.doc_count = self.env['ir.attachment'].search_count(domain)

    @api.multi
    def attachment_tree_view(self):
        domain = [('res_model', '=', self._name), ('res_id', 'in', self.ids)]
        return {
            'name': 'Documente',
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        }

    @api.model
    def default_get(self, fields_list):
        defaults = super(PropertyProperty, self).default_get(fields_list)

        defaults['country_id'] = self.env.user.company_id.partner_id.country_id.id
        return defaults

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            return {'domain': {'state_id': [('country_id', '=', self.country_id.id)]}}
        else:
            return {'domain': {'state_id': []}}
