# coding=utf-8


from odoo import models, fields, api
from datetime import datetime


class PropertyLand(models.Model):
    _name = 'property.land'
    _description = "Land"
    _inherit = 'property.property'

    location_type = fields.Selection([('I', 'Intravilan'), ('E', 'Extravilan')], default='E')

    tarla = fields.Char()  # required=True)
    parcela = fields.Char(string="Parcela cadastrală")
    sector = fields.Char(string="Sector cadastral")
    bloc_fizic = fields.Char(string="Nr bloc fizic")

    carte = fields.Char(string="Carte funciară")
    utr = fields.Char(string="UTR")
    categ_id = fields.Many2one('property.land.categ', string="Category")


    cod = fields.Char()
