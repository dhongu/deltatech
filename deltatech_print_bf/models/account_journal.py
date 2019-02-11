# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'


    cod_ecr = fields.Char(string='Cod ECR', default='1', size=1)


    '''
 1 - plata cu numerar
 2 - plata cu card
 4 - subtotal
 8 - plata in valuta alternativa si restul in valuta de baza
 9 - plata in valuta alternativa si restul in valuta alternativa
    '''