Features:
 - Update purchase price after receipt
 - If the product has FIFO cost, the product standard_price will be overwritten
 - Depends on system parameters:
    - *purchase.update_product_price* - if set to False, the product seller price will not be modified, if set to True, the
      product seller price will be overwritten
    - *purchase.add_supplier_to_product* - if set to True, the supplier and the price will be automatically added to the
      supplier info of the product, if set to False, no modifications will be made in the supplier info of the product
    - *purchase.update_list_price* - if set to True, the list price will be updated according to trade markup value.
      If set to False, the list price will not be updated
    - *sale.list_price_round* - decimal number to which the list price is rounded
 - New fields added in product template:
    - last_purchase_price - last purchase price. It's updated at receipt validation
    - trade_markup - trade parkup for the product. It can be updated with a wizard (Action->Set trade markup)
 - New feature:
    - if trade_markup **is set** for a product, at reception the sale price will be computed from last_purchase_price and trade_markup
