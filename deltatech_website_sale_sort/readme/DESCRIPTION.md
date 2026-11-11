Shoppers like to start with what others buy, visit and rate highly, or with what is in stock. This module adds five such criteria to the product sort options of the website and keeps the figures behind them up to date with a daily scheduled action.

- **New sort options**: *Best sellers*, *Most Visited*, *Reviews*, *Best Review* and *Availability* join the website's product sort list, each with the highest value first.
- **Sales and visits**: *Best sellers* uses the quantity sold in the last 365 days, read from the sales report for its done states. *Most Visited* uses the visits recorded for the product page.
- **Ratings**: *Reviews* orders products by the number of ratings submitted for them, and *Best Review* by their average.
- **Stock status**: *Availability* puts first the products whose on-hand quantity is above zero.
- **Daily refresh**: The scheduled action *Products: Update products statistics* recomputes the figures once a day for every product and variant, in batches of 2,000, as queued jobs when `queue_job` is installed.

It depends on *eCommerce* (`website_sale`) and *Inventory*. The figures are stored on products and variants, so new sales, visits and ratings count in the sort only after the next run; archived products are skipped. The action runs as the system user and the module has no security groups.
