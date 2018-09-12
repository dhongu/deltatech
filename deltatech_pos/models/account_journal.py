# coding=utf-8


from odoo import fields, models, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'


    cod_ecr = fields.Char(string='Cod ECR', default='1', size=1)