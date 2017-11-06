# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _

selection_level = [('p', 'P'), ('m', 'M'), ('s', 'S')] + [(num, str(num)) for num in range(1, 30)]


class PropertyRoom(models.Model):
    _name = 'property.room'
    _description = "Room"

    name = fields.Char(string="Number")
    building_id = fields.Many2one('property.building', string='Building', required=True)

    level = fields.Selection(selection_level)

    height = fields.Float()
    perimeter = fields.Float()
    surface_disinsection = fields.Float(string="Area of disinsection", compute="_compute_surface_disinsection", store=True)

    surface = fields.Float("Surface area")
    surface_cleaning_floor = fields.Float(string="Surface cleaning floor")
    surface_cleaning_doors = fields.Float(string="Surface cleaning doors")
    surface_cleaning_windows = fields.Float(string="Surface cleaning window")



    floor_type = fields.Selection([('c', 'Carpet'), ('l', 'Linoleum'), ('w', 'Wood')])

    usage = fields.Selection([
        ('office', 'Office'),
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
    ], string="Room usage", help="The purpose of using the room")

    rented_room = fields.Boolean()
    tenant_id = fields.Many2one('res.partner', string="Tenant")

    last_maintenance = fields.Date()
    technical_condition = fields.Selection([(0,'Missing'),(1,'Unsatisfactory'),(3,'good'),(5,'very good')],
                                           group_operator='avg')





    @api.multi
    @api.depends('surface', 'height', 'perimeter')
    def _compute_surface_disinsection(self):
        for room in self:
            room.surface_disinsection = 2 * room.surface + room.height * room.perimeter

    @api.constrains
    def _check_cleaning_surface(self):
        if self.cleaning_surface > self.surface:
            raise ValidationError(_('Cleaning surface most by lower that surface area'))



