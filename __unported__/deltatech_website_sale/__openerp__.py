{
    'name': 'Deltatech eCommerce extension',
    'category': 'Website',
    'summary': 'Sell Your Products Online',
    'website': 'https://www.odoo.com/page/e-commerce',
    'version': '1.0',
    'description': """
OpenERP E-Commerce Extension
============================
- adugata posbilitatea de a afisa daca produsul este dispoibil in stoc
 
        """,
    'author': 'Dorin Hongu',
    'depends': ['website', 'website_sale'],
    'data': [
        'product_view.xml',
        'views/templates.xml',

    ],
    'demo': [
        #'data/demo.xml',
    ],
 
    'installable': True,
    'application': False,
}
