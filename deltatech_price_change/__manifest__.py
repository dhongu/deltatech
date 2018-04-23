# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Price",
    "version": "1.0",
    "author": "Deltatech",
    "website": "",
    "description": """
 
Scopul modulului este de a controla modificarile de pret la produse.
La fiecare modificare de pret intocmeste un document care este datat si numerotat.


Trebuie configurat TVA de vanzare ca fiind inclus in pret

Product
-------
    * a fost adaugat un camp nou last_purchase_price in care este stocat ultimul pret de achizitie. 
    * campul lst_price a fost facut read only.  <- prblema e ca se poate edita din website_sale
Nota
    * campul list_price - este editabil in template si este editbil si sta la baza determinarii pretului
    * campul lst_price  - este pretul calculat si apare la variantele de produs

Purchase order
--------------
    * la nivel de line am adaugat campul list_price care adus in mod automat la modificare un produs !
    * dupa confirmarea unei comenzi de achizitie se suprascriere aceasta valoare.
    * obs de vazut daca se poate actuliza diferit pretul pe fiecare furnizor 
    
    
Trebuie definita o regula de pret noua prin care se aduce pretul din campul last_purchase_price    

    """,

    "category": "Generic Modules",
    "depends": ["base", "stock", "product", "sale", "purchase"],

    "data": [
        # "views/product_view.xml",
        # "views/purchase_view.xml",
        "views/product_price_change_view.xml",
        # "views/purchase_report.xml",
        "views/price_change_report.xml",
        "views/report_pricechange.xml",
        # "views/report_receivepurchaseorder.xml",
        'security/ir.model.access.csv'
    ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
