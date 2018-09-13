# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AbstractReportXslx(models.AbstractModel):
    _name = 'report.abstract_attendance_summary_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def __init__(self, pool, cr):
        # main sheet which will contains report
        self.sheet = None

        # columns of the report
        self.columns = None

        # row_pos must be incremented at each writing lines
        self.row_pos = None

    def get_workbook_options(self):
        return {'constant_memory': True}

    def generate_xlsx_report(self, workbook, data, objects):
        report = objects

        self.row_pos = 0

        self._define_formats(workbook)

        report_name = self._get_report_name()
        filters = self._get_report_filters(report)
        self.columns = self._get_report_columns(report)

        self.sheet = workbook.add_worksheet(report_name[:31])

        self._set_column_width()

        self._write_report_title(workbook, report_name)

        self._write_filters(workbook, filters)

        self._generate_report_content(workbook, report)

    def _define_formats(self, workbook):
        """ Add cell formats to current workbook.
        Those formats can be used on all cell.

        Available formats are :
         * format_bold
         * format_right
         * format_right_bold_italic
         * format_header_left
         * format_header_center
         * format_header_right
         * format_header_amount
         * format_amount
         * format_percent_bold_italic
        """
        self.format_bold = workbook.add_format({'bold': True})
        self.format_right = workbook.add_format({'align': 'right'})
        self.format_right_bold_italic = workbook.add_format(
            {'align': 'right', 'bold': True, 'italic': True}
        )
        self.format_header_left = workbook.add_format(
            {'bold': True,
             'border': True,
             'bg_color': '#FFFFCC'})
        self.format_header_center = workbook.add_format(
            {'bold': True,
             'align': 'center',
             'border': True,
             'bg_color': '#FFFFCC'})
        self.format_header_right = workbook.add_format(
            {'bold': True,
             'align': 'right',
             'border': True,
             'bg_color': '#FFFFCC'})
        self.format_header_amount = workbook.add_format(
            {'bold': True,
             'border': True,
             'bg_color': '#FFFFCC'})
        self.format_header_amount.set_num_format('#,##0.00')
        self.format_amount = workbook.add_format()
        self.format_amount.set_num_format('#,##0.00')
        self.format_percent_bold_italic = workbook.add_format(
            {'bold': True, 'italic': True}
        )
        self.format_percent_bold_italic.set_num_format('#,##0.00%')

    def _set_column_width(self):
        """Set width for all defined columns.
        Columns are defined with `_get_report_columns` method.
        """
        for position, column in self.columns.items():
            self.sheet.set_column(position, position, column['width'])

    def _write_report_title(self, workbook, title):
        """Write report title on current line using all defined columns width.
        Columns are defined with `_get_report_columns` method.
        """
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, len(self.columns) - 1,
            title, workbook.add_format({'bold': True})
        )
        self.row_pos += 3

    def _write_filters(self, workbook, filters):
        """Write one line per filters on starting on current line.
        Columns number for filter name is defined
        with `_get_col_count_filter_name` method.
        Columns number for filter value is define
        with `_get_col_count_filter_value` method.
        """
        col_name = 1
        col_count_filter_name = self._get_col_count_filter_name()
        col_count_filter_value = self._get_col_count_filter_value()
        col_value = col_name + col_count_filter_name + 1
        for title, value in filters:
            self.sheet.merge_range(
                self.row_pos, col_name,
                self.row_pos, col_name + col_count_filter_name - 1,
                title, workbook.add_format(
                    {'bold': True,
                     'border': True,
                     'bg_color': '#FFFFCC'}))
            self.sheet.merge_range(
                self.row_pos, col_value,
                self.row_pos, col_value + col_count_filter_value - 1,
                value)
            self.row_pos += 1
        self.row_pos += 2

    def write_array_title(self, workbook, title):
        """Write array title on current line using all defined columns width.
        Columns are defined with `_get_report_columns` method.
        """
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, len(self.columns) - 1,
            title, workbook.add_format({'bold': True})
        )
        self.row_pos += 1

    def write_array_header(self, workbook):
        """Write array header on current line using all defined columns name.
        Columns are defined with `_get_report_columns` method.
        """
        for col_pos, column in self.columns.items():
            color = column.get('color', '#FFFFCC')
            self.sheet.write(self.row_pos, col_pos, column['header'],
                             workbook.add_format(
                                 {'bold': True,
                                  'align': 'center',
                                  'border': True,
                                  'bg_color': color}))
        self.row_pos += 1

    def write_line(self, workbook, line_object, formats):
        """Write a line on current line using all defined columns field name.
        Columns are defined with `_get_report_columns` method.
        """
        for col_pos, column in self.columns.items():
            value = getattr(line_object, column['field'])
            cell_type = column.get('type', 'string')
            if cell_type == 'string':
                self.sheet.write_string(self.row_pos, col_pos, value or '',workbook.add_format(formats))
            elif cell_type == 'amount':
                self.sheet.write_number(
                    self.row_pos, col_pos, float(value),
                    workbook.add_format(formats)
                )
        self.row_pos += 1

    def _generate_report_content(self, workbook, report):
        pass

    def _get_report_name(self):
        """
            Allow to define the report name.
            Report name will be used as sheet name and as report title.

            :return: the report name
        """
        raise NotImplementedError()

    def _get_report_columns(self, report):
        """
            Allow to define the report columns
            which will be used to generate report.

            :return: the report columns as dict

            :Example:

            {
                0: {'header': 'Simple column',
                    'field': 'field_name_on_my_object',
                    'width': 11},
                1: {'header': 'Amount column',
                     'field': 'field_name_on_my_object',
                     'type': 'amount',
                     'width': 14},
            }
        """
        raise NotImplementedError()

    def _get_report_filters(self, report):
        """
            :return: the report filters as list

            :Example:

            [
                ['first_filter_name', 'first_filter_value'],
                ['second_filter_name', 'second_filter_value']
            ]
        """
        raise NotImplementedError()

    def _get_col_count_filter_name(self):
        """
            :return: the columns number used for filter names.
        """
        raise NotImplementedError()

    def _get_col_count_filter_value(self):
        """
            :return: the columns number used for filter values.
        """
        raise NotImplementedError()
