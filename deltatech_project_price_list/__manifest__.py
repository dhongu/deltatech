# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    'name': 'Deltatech Project Pricelist',
    'summary': 'Project-level pricelist used when creating Sales Orders from a project',
    'version': '19.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    'category': 'Sales/Project',
    'license': 'LGPL-3',
    'depends': [
        'sale_project',  # brings project + sale integration
    ],
    'data': [
        'views/project_views.xml',
    ],
    'installable': True,
    'application': False,
}
