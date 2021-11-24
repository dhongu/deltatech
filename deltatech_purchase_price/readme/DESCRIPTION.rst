Features:
 - Update purchase price after receipt
 - If the product has average cost, the cost will be overwritten (if parameter set to True)

 - New fields added in product template:
    - last_purchase_price - last purchase price. It's updated at receipt validation
    - trade_markup - trade parkup for the product. It can be updated with a wizard (Action->Set trade markup)
 - New feature:
    - if trade_markup **is set** for a product, at reception the sale price will be computed from last_purchase_price and trade_markup
