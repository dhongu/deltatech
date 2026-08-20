- Features:

  - New technical access group to hide margin and purchase price in sale order
  - New technical access group to prevent changing price in sale order
  - New technical access group to allow sale price below the purchase price
  - Warning/Error on sale order if sale price is below the purchase price
  - Configurable reaction per company (Settings > Sales > Pricing): block the
    sale, warn only, or no check. "Warn only" flags the line and shows a banner
    without ever blocking - for businesses where selling below cost is a routine
    part of the trade (perishable goods, stock clearance, commercial gestures).
  - The cost is compared in the unit of the sale order line, and the comparison
    stays silent when the line unit and the product base unit belong to different
    unit families - Odoo 19 converts any pair of units by their absolute factors,
    so a wrong `uom_id` would otherwise report every line as below cost.

sale.margin_limit and sale.margin_limit_check_validate are configurable from
Settings > Sales. sale.margin_limit is the margin percentage below which a line is
reported: 0 reports only negative margins, a negative value tolerates a loss of up
to that percentage, a positive value also reports thin but positive margins.

sale.check_price_website - parmanetru pentru verificare pret pentru comenzile de pe website
sale.margin_limit_check_validate - system parameter - if set, the verificaion is made at order confirmation (users with
no rights to sell below margin/purchase price can still create draft sale orders)
