##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
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


import xlwt
from datetime import datetime
from openerp.osv import orm
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell, _render
from openerp.tools.translate import translate, _
import logging
_logger = logging.getLogger(__name__)

_ir_translation_name = 'purchase.order.xls'


class purchase_order_xls_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(purchase_order_xls_parser, self).__init__(cr, uid, name, context=context)
        purchase_obj = self.pool.get('purchase.order')
        self.context = context
        #wanted_list = purchase_obj._report_xls_fields(cr, uid, context)
        #template_changes = purchase_obj._report_xls_template(cr, uid, context)
        
        self.localcontext.update({
            'datetime': datetime,
             'wanted_list': ['name','desc','unit','product_qty'],
            #'template_changes': template_changes,
            '_': self._,
        })

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(self.cr, _ir_translation_name, 'report', lang, src) \
            or src


class purchase_order_xls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(purchase_order_xls, self).__init__(  name, table, rml, parser, header, store)

        # Cell Styles
        _xs = self.xls_styles
        # header
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        self.rh_cell_style_right = xlwt.easyxf(rh_cell_format + _xs['right'])
        # lines
        aml_cell_format = _xs['borders_all']
        self.aml_cell_style = xlwt.easyxf(aml_cell_format)
        self.aml_cell_style_center = xlwt.easyxf(aml_cell_format + _xs['center'])
        self.aml_cell_style_date = xlwt.easyxf( aml_cell_format + _xs['left'], num_format_str=report_xls.date_format)
        self.aml_cell_style_decimal = xlwt.easyxf( aml_cell_format + _xs['right'],  num_format_str=report_xls.decimal_format)

        # totals
        rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rt_cell_style = xlwt.easyxf(rt_cell_format)
        self.rt_cell_style_right = xlwt.easyxf(rt_cell_format + _xs['right'])
        self.rt_cell_style_decimal = xlwt.easyxf( rt_cell_format + _xs['right'], num_format_str=report_xls.decimal_format)
        
        self.col_specs_template = {
            'name': {
                'header': [1, 12, 'text', _render("_('Item No.')")],
                'lines': [1, 0, 'text', _render("line.product_id.default_code or ''")] },
            'desc': {
                'header': [1, 42, 'text', _render("_('Description')")],
                'lines': [1, 0, 'text', _render("line.product_id.name_template or ''")] },
            'unit': {
                'header': [1, 20, 'text', _render("_('Unit of measure')")],
                'lines': [1, 0, 'text', _render("'PCS'")] },
            'product_qty': {
                'header': [1, 10, 'text', _render("_('Quantity')"), None, self.rh_cell_style_right],
                'lines': [1, 0, 'number', _render("line.product_qty")] },
        }

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        wanted_list = _p.wanted_list
        
        _ = _p._

          # report_name = objects[0]._description or objects[0]._name
        report_name = _("Purchase Order")
        ws = wb.add_sheet("Data")
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        for order in objects:
            # Title
            cell_style = xlwt.easyxf(_xs['xls_title'])
            c_specs = [ ('report_name', 1, 0, 'text', report_name+':'+order.name) ]           
            row_data = self.xls_row_template(c_specs, ['report_name'])
            #row_pos = self.xls_write_row( ws, row_pos, row_data, row_style=cell_style)
            #row_pos += 1
            # Column headers
            c_specs = map(lambda x: self.render(x, self.col_specs_template, 'header', render_space={'_': _p._}),  wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row( ws, row_pos, row_data, row_style=self.rh_cell_style, set_column_size=True)
                           
            for line in order.order_line:
                c_specs = map(lambda x: self.render(x, self.col_specs_template, 'lines'), wanted_list)
                row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row( ws, row_pos, row_data, row_style=self.aml_cell_style )
        
            #date romsystems
            font0 = xlwt.Font()
            font0.bold = True
            style0 = xlwt.XFStyle()
            style0.font = font0
            ws.col(5).width = 256*20
            ws.col(6).width = 256*25
            ws.write(3, 5, 'Denumire Client',style0)
            ws.write(3, 6, 'SC ROMSYSTEMS SRL')
            ws.write(4, 5, 'Cod Client',style0)
            ws.write(4, 6, 'CL022842')
            ws.write(5, 5, 'Mod Livrare',style0)
            ws.write(6, 5, 'Observatii',style0)

purchase_order_xls('report.purchase.order.xls',
              'purchase.order',
              parser=purchase_order_xls_parser)
