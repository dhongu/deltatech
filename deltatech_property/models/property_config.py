# coding=utf-8


from odoo import models, fields, api
from datetime import datetime


class PropertyNomenclature(models.AbstractModel):
    _name = 'property.nomenclature'
    _description = "Nomenclature"
    _rec_name = 'display_name'
    _order = 'cod'

    display_name = fields.Char(string='Name', compute='_compute_display_name', store=True, index=True)
    cod = fields.Char(string='Cod rand')
    name = fields.Char()
    categ = fields.Char(string="Category")
    parent_id = fields.Char(string='Parent')

    @api.multi
    @api.depends('cod')
    def _compute_display_name(self):
        for item in self:
            if self.cod:
                item.display_name = '%s - %s' % (item.cod, item.name)
            else:
                item.display_name = item.name

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if not name.isdigit():
            return super(PropertyNomenclature, self).name_search(name, args, operator, limit)

        recs = self.search([('cod', operator, name.zfill(2))], limit=1)
        return recs.name_get()


class PropertyAcquisition(models.Model):
    _name = 'property.acquisition'
    _description = "Property Acquisition"
    _inherit = 'property.nomenclature'


class PropertyLandCategory(models.Model):
    _name = 'property.land.categ'
    _description = "Property Land Category"
    _inherit = 'property.nomenclature'


class PropertyBuildingCategory(models.Model):
    _name = 'property.building.categ'
    _description = "Property Building Category"
    _inherit = 'property.nomenclature'


class PropertyBuildingPurpose(models.Model):
    _name = 'property.building.purpose'
    _description = "Purpose building"
    _inherit = 'property.nomenclature'

    parent_id = fields.Many2one('property.building.purpose')


class PropertyCostCenter(models.Model):
    _name = 'property.cost.center'
    _description = "Property Cost Center"
    _inherit = 'property.nomenclature'


class PropertyRegion(models.Model):
    _name = 'property.region'
    _description = "Property Region"
    _inherit = 'property.nomenclature'




class PropertyRoomUsage(models.Model):
    _name = 'property.room.usage'
    _description = "Property Room Usage"
    _inherit = 'property.nomenclature'

    categ = fields.Selection([
        ('office', 'office'),
        ('meeting', 'Meeting room'),
        ('kitchens', 'Kitchens'),
        ('laboratory','Laboratory'),
        ('garage','Garage'),
        ('archive', 'Archive'),
        ('warehouse', 'Warehouse'),
        ('log_warehouse', 'Logistics warehouse'),
        ('it_endowments', 'IT endowments (Ranks, Hall Servers)'),
        ('premises', 'Technical premises (thermal, air conditioning, post-transformer)'),
        ('cloakroom', 'Cloakroom'),
        ('sanitary', 'Sanitary group'),
        ('access', 'Access ways'),
        ('lobby', 'Lobby'),
        ('staircase', 'Staircase'),
    ])
