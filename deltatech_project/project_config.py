# -*- coding: utf-8 -*-


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp


class project_config(models.Model):
    _name = 'project.config'
    
    
    use_equal_distribution_percentage = fields.Boolean('Use the equal distribution percentage between task' )
