## 19.0.1.0.2

- Security: `/shop/confirmation` no longer confirms any order from the session. The order is
  confirmed only when it is a quotation with a `done`/`authorized` payment transaction, or a
  `pending` one on a provider without online processing (wire transfer, cash on delivery).
  Reloading the page on an already confirmed order no longer raises an error.
