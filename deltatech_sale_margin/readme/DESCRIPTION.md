  - Features:
    
      - New technical access group to hide margin and purchase price in
        sale order
      - New technical access group to prevent changing price in sale
        order
      - New technical access group to allow sale price below the
        purchase price
      - Warning/Error on sale order if sale price is below the purchase
        price

sale.check\_price\_website - parmanetru pentru verificare pret pentru
comenzile de pe website sale.margin\_limit\_check\_validate - system
parameter - if set, the verificaion is made at order confirmation (users
with no rights to sell below margin/purchase price can still create
draft sale orders)
