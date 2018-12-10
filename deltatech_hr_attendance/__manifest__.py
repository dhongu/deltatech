# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Prezenta",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 
 
 

    """,

    "category": "Human Resources",
    "depends": [
        "hr_attendance",
        "hr_holidays",
        "report_xlsx",
        "date_range"
        # "web_grid"
    ]
    ,

    "data": [
        'views/hr_attendance_view.xml',
        'views/hr_attendance_sheet_view.xml',
        'views/hr_view.xml',
        'wizard/hr_attendance_import_view.xml',
        'wizard/hr_meal_tickets_view.xml',
        'wizard/hr_attendance_summarry_view.xml',
        'wizard/hr_leaves_summary_view.xml',
        'security/hr_attendance_sheet_security.xml',
        'report/hr_attendance_reports.xml',
        'report/hr_attendance_templates.xml',
        'security/ir.model.access.csv',
    ],

    "active": False,
    "installable": True,
}
