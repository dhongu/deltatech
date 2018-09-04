{
    'name': 'Deltatech eCommerce extension',
    'category': 'Website',
    'summary': 'Sell Your Products Online',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    'version': '1.0',
    'description': """
OpenERP E-Commerce Extension
============================
- adugata posbilitatea de a afisa daca produsul este dispoibil in stoc
- inregistreaza istoricul cautarilor din magazin

        """,

    'depends': ['website', 'website_sale'],
    'data': [
        'views/product_view.xml',
        'views/templates.xml',
        'views/website_keyword_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        # 'data/demo.xml',
    ],

    'installable': True,
    'application': False,
}
