# -*- coding: utf-8 -*-


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp


class website_user_search(models.Model):
    _name = 'website.user.search'
    _description = 'User search history'
    _order = 'date desc'

    user_id = fields.Many2one('res.users', string='User')
    date = fields.Datetime()
    word = fields.Char()
