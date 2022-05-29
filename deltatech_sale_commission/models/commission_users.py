# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class CommissionUsers(models.Model):
    _name = "commission.users"
    _description = "Users commission"

    user_id = fields.Many2one("res.users", string="Salesperson", required=True)
    name = fields.Char(string="Name", related="user_id.name")
    rate = fields.Float(string="Rate", default=0.01, digits=(12, 3))
    manager_rate = fields.Float(string="Rate manager", default=0, digits=(12, 3))
    manager_user_id = fields.Many2one("res.users", string="Sales Manager")
    director_rate = fields.Float(string="Rate director", default=0, digits=(12, 3))
    director_user_id = fields.Many2one("res.users", string="Sales Director")
    journal_id = fields.Many2one("account.journal", string="Journal", domain="[('type', 'in', ['sale','sale_refund'])]")
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
