The figures behind the new sort options are computed once a day by a scheduled action. Until its
first run they are all zero, and the new options do not change the order of the products.

1. Open the shop (the *Shop* menu of the website, or `/shop`) and click *Sort By*. Below the
   standard Odoo options, the module adds *Best sellers*, *Most Visited*, *Reviews*, *Best Review*
   and *Availability*. Every visitor of the website sees the same list.

   ![The Shop page with the Sort By list open: below Featured, Newest Arrivals, Name (A-Z) and the two price sorts, the options Best sellers, Most Visited, Reviews, Best Review and Availability are highlighted](static/description/en/01_optiuni_sortare.png)

2. Pick *Best sellers*. The *Sort By* button shows the chosen option, and the first products are
   the ones with the highest quantity on confirmed sales orders in the last 365 days. The other
   options work the same way: *Most Visited* uses the visits on the product page, *Reviews* and
   *Best Review* the number and the average of the ratings, *Availability* the on-hand stock.

   ![The Shop page sorted by Best sellers: the Sort By button shows the chosen option and the first three products are Scaun de birou ergonomic, Birou reglabil electric and Lampă de birou LED, in the order of the quantities sold](static/description/en/02_magazin_cele_mai_vandute.png)

3. To make one of them the default sort of the shop, click *Editor* (top left) on the *Shop* page,
   then *Edit*, and click the product grid. In the right panel, on the *Style* tab, choose it in *Default Sort* and click
   *Save*. Visitors who do not pick a sort themselves now see the products in that order.

   ![The website editor on the Shop page: on the Style tab of the right panel, the Default Sort field under Toolbar is highlighted, with the value Featured](static/description/en/03_sortare_implicita_editor.png)

4. With developer mode on, go to *Settings > Technical > Automation > Scheduled Actions* and open
   *Products: Update products statistics*. It runs once a day and recomputes, for every active
   product, the sales and visits of its variants (archived ones included, refreshed in the same
   batch before they are summed), the ratings and the stock. *Run Manually* computes the figures at
   once, which is useful right after installing the module. With
   `queue_job` installed the work is split into queued jobs, and the new order shows once they
   are done.

   ![The form of the scheduled action Products: Update products statistics: model Product, Execute Every 1 Days highlighted and the Run Manually button highlighted](static/description/en/04_actiune_planificata.png)
