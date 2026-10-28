Technical base for the modules that read **product pages on the web**: the pages of the
competitors, the pages of the vendors that give no feed. It has no menu and no data of its own;
the modules that use it decide what to read and what to write.

## Safe reading

- **Public addresses only**: an http(s) address is read only when its host resolves to public IP
  addresses. Loopback, private networks, link-local and cloud metadata addresses are refused, and the
  address the connection really reaches is checked again when it opens, so a DNS answer changed in
  between is refused too.
- **Redirects checked**: they are followed by hand, at most 5, each one checked the same way.
- **Limited size**: a page is read in pieces and cut at 3 MiB; a content type that is not expected
  is refused.

## Polite reading

- **robots.txt** is respected: a page that the site forbids is not read (state *Blocked*). It can be
  turned off by the module that uses the base, per site.
- **A pause** is kept between two requests to the same site; the scheduled reading takes the sites
  in turn, so that the pause of one site is spent on the others.
- **No way around protections**: a page of protection against robots (CAPTCHA, Cloudflare challenge,
  403, 429) only gives the state *Blocked*. Nothing tries to get around it: ask the site for a feed
  or an API instead.

## What is read from a page

- **schema.org data** (JSON-LD and Microdata): name, brand, SKU, MPN, barcode (GTIN), images,
  description and the offers, with their price, currency and availability. When there are several
  offers, the cheapest one in stock is kept.
- **Selectors** (XPath, CSS, regular expression, JSON-LD path) configured for the sites without
  schema.org data, with a table of values (for example *In stock* → in stock).
- **The usual HTML patterns**, as a last resort, for the price only; the old, struck through prices
  are left out. A price found this way is marked as such.
- **Prices written the Romanian or the English way**: `1.299,00 lei`, `1,299.00`, `1 299,99`.

## Checks

- **Another product**: a page that declares another barcode, or another code (compared without
  spaces, dashes and dots), than the product expected gets the state *Other Product*.
- **Jump of price**: a price that changed more than a set percentage since the previous reading
  gets the state *Suspect* and waits for a confirmation.

## For the developers

- `web.scan.source.mixin`: a page read again and again, with its state, its last reading and the
  failed readings in a row; the scheduled action skips a page after 5 failures.
- `web.scan.history.mixin`: the history of the values shown by a page, as intervals: a new line only
  when a value changes, otherwise the last line is extended.
- `utils.fetch`, `utils.extract`, `utils.codes`, `utils.scan`: the same functions without the
  database.
