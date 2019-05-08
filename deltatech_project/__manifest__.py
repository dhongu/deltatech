# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Project Extension",
    "version": "1.10",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",

    'category': 'Project Management',

    "depends": ["project",'web_kanban_gauge'],


    "license": "LGPL-3",
    "data": [
        'views/report_project_do_today.xml',
        'wizard/print_report_date_view.xml',
        "views/project_view.xml",

        'wizard/recurrence_view.xml',
        'wizard/task_set_progress_view.xml',
        'views/res_config_view.xml',

        "data/project_data.xml",

    ],
    "images": ['images/main_screenshot.png'],
    "active": False,
    "installable": True,

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
