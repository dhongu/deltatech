# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################



from openerp.exceptions import except_orm, Warning, RedirectWarning, ValidationError
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
import openerp.addons.decimal_precision as dp


class product_template(models.Model):
    _inherit = 'product.template' 

    @api.one
    @api.constrains('seller_ids','purchase_ok')
    def _check_description(self):
        if self.purchase_ok  and self.type == 'product':
            if not self.seller_ids:
                raise ValidationError(_("No defined a supplier of this product"))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
