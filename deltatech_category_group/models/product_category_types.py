# ©  2023-now Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import fields, models


class CategoryGroupType(models.Model):
    _name = "category.group.type"
    _description = "Category group type"
    _order = "sequence, name"

    name = fields.Char(string="Category type")
    sequence = fields.Integer(string="Sequence", default=10)


class CategoryGroupClass(models.Model):
    _name = "category.group.class"
    _description = "Category group class"
    _order = "sequence, name"

    name = fields.Char(string="Category class")
    sequence = fields.Integer(string="Sequence", default=10)
