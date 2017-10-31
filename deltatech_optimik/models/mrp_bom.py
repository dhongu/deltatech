# coding=utf-8


from odoo import models, fields, api
from odoo.exceptions import ValidationError


ITEM_CATEG = [('cut', 'Cut'),
              ('cut_fiber', 'Fiber cut'), #cut_grain
              ('normal', 'Normal'),
              ('left', 'Left'),
              ('right', 'Right'),
              ('top', 'Top'),
              ('bottom', 'Bottom')]


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    item_categ = fields.Selection(ITEM_CATEG, default='normal', string='Item Category')
    #daca specifica ca este linie de un cant atunci trebuie sa specific la ce material (pozitie din lista) se aplica acel cant
    # sa se tine cont de ordonarea pozitiilor din lista ?

    """
    @api.one
    @api.constrains('item_categ')
    def _check_item_categ(self):
        if self.item_categ != 'normal':
            for item in self.bom_id.bom_line_ids:
                if item.id != self.id and self.item_categ == item.item_categ:
                    raise ValidationError("There can be two positions with the %s category" % item.item_categ)
    """