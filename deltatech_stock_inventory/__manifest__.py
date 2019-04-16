# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

#     In versiunea 10.0 era si
#     Afisare valoare de vanzare in rapotul de pozitii de stoc (evaluare inventar) si stoc la data

{
    "name": "Deltatech Stock Inventory",
    'version': '11.0.1.0.0',
    "author" : "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

     Afisare coloana de pret de stoc la inventariere
     

 
    """,
    "category": "Warehouse",
    "depends": [ 'deltatech_stock_date', "stock_account"],

    "data": [
        'data/data.xml',
        'views/stock_view.xml',
        'views/product_view.xml',
        'views/report_stockinventory.xml'
    ],
    "images": ['images/main_screenshot.png'],
    "installable": True,
}
