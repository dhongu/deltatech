Keep the prices of your competitors next to your own product, and read the
current price from the competitor's web page with one click, instead of checking
the sites by hand and copying the prices into spreadsheets.

**Competitor lines on the product.** Adds a **Competitor Prices** tab on the
product form. Each line holds the **Competitor** name, the **Product URL** on the
competitor's site, the **Last Price** and its **Currency**, the **Last Fetch**
date and the **Fetch Status** message.

**Fetch on demand.** The **Fetch** button on a line downloads the competitor page
and writes the price found, the time of the fetch and the status *OK*. When the
page states a currency that exists in your database (for example EUR or USD),
the line currency is updated too.

**Price extraction.** The price is read first from the structured product data of
the page (JSON-LD or Microdata, *Offer* and *AggregateOffer*). When the page has
none, common HTML patterns are tried: the `product:price:amount` meta tag, the
`itemprop="price"` attribute and elements whose class contains "price". Both
decimal styles (1.234,56 and 1,234.56) are understood.

**Clear errors.** When no price is found, or the page cannot be loaded (for
example 403 or 404), the line keeps its last price and the reason is shown in
**Fetch Status**.

**Only public addresses.** The server fetches only http(s) addresses that resolve
to public IP addresses, and checks every redirect, so a URL cannot be used to
reach internal services.

## Usage

Open a product, go to the **Competitor Prices** tab, add a line with the
competitor name and the product URL, save, then click **Fetch** on the line.

Internal users can read, create, edit and delete competitor lines.

## Limitations

- Prices are fetched one line at a time; there is no button that fetches all the
  lines of a product.
- There is no scheduled fetch. The **Auto Fetch** column (hidden by default)
  only marks lines and has no effect.
- Sites that load the price with JavaScript, or that block automated requests,
  return no price.
