Features:
 - Update purchase price after receipt
 - If the product has average cost, the cost will be overwritten (if parameter set to True)
 - Depends on system parameters:
    - *purchase.update_product_price* - if set to False, the product price will not be modified, if set to True, the
      product price will be allways overwritten
    - *purchase.add_supplier_to_product* - if set to True, the supplier and the price will be automatically added to the
      supplier info of the product, if set to False, no modifications will be made in the supplier info of the product
