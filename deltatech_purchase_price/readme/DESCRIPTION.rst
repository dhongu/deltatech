Features:
 - Update purchase price after receipt
 - If the product has average cost, the cost will be overwritten (if parameter set to True)
 - Depends on system parameters:
    - *purchase.update_product_price* - if set to False, the product price will not be modified, if set to True, the
      product price will be allways overwritten
    - *purchase.add_supplier_to_product* - if set to True, the supplier and the price will be automatically added to the
      supplier info of the product, if set to False, no modifications will be made in the supplier info of the product
 - New fields added in product template:
    - last_purchase_price - last purchase price. It's updated at receipt validation
    - trade_markup - trade parkup for the product. It can be updated with a wizard (Action->Set trade markup)
 - New feature:
    - if trade_markup **is set** for a product, at reception the sale price will be computed from last_purchase_price and trade_markup
