# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

from . import registry_office_common


class RegistryOfficDocType(models.Model):
    _name = 'registry.office.doc_type'
    _description = "Document Type"

    name = fields.Char()
    solution_deadline = fields.Integer()  # Termen de rezolvare


class RegistryOfficFolder(models.Model):
    _name = 'registry.office.folder'
    _description = "Folder"

    name = fields.Char()


# mod de expediere
class RegistryOfficShipment(models.Model):
    _name = 'registry.office.shipment'
    _description = "Mode of shipment"

    name = fields.Char()


"""
curier
direct
email
fax
posta recomandata, posta confirmare de primire, posta strainatate 
"""
