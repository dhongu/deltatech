- Features:

  - New technical access group for display margin and purchase price in customer invoice
  - Technical access group to prevent changing price in customer invoice
  - New technical access group to allow sale price below the purchase price
  - Warning/Error on customer invoice if sale price is below the purchase price
  - New report for analysis profitability
  - Calculation of sales commissions on sale order salesperson or invoice salesperson (configurable)
  - Added parameter "deltatech_sale_commission.days_for_commission", the value should be an integer
  - When the parameter is set when the commission is calculated, the system will check if the invoice is _fully paid_
    and if the difference between the date of the last payment and the due date is less than the value of the parameter
  - If the difference is grater than the value of the parameter, the commission will be 0
