# Sale Payment

Adds full payment visibility directly on the sale order, without having to open invoices or payment transactions.

## Features

### Payment button on sale order
Generates a payment link directly from the sale order, automatically computing the remaining amount due (order total minus amount already paid on posted invoices).

### Payment fields on sale order

| Field | Description |
|---|---|
| `payment_amount` | Total amount paid (done transactions + paid/partial invoices) |
| `payment_status` | Payment status (see below) |
| `provider_id` | Payment provider used (Stripe, PayPal, etc.) |

All fields are **stored in the database** (`store=True`) — filtering and sorting use SQL directly, with no recomputation on every query.

### Payment statuses

| Status | Description |
|---|---|
| `without` | No payment transaction on the order |
| `initiated` | Transaction in `draft` or `error` state |
| `pending` | Transaction awaiting confirmation (e.g. bank transfer) |
| `authorized` | Amount authorized (held) but not yet captured |
| `partial` | Order partially paid |
| `done` | Order fully paid |
| `cancelled` | Transaction cancelled |

### `payment_amount` computation logic

- **`done` transactions** — summed directly
- **`paid`/`partial` invoices** — the reconciled amount is added (`amount_total_signed − amount_residual_signed`); post-processed transactions for those invoices are removed from `done_tx` to avoid double counting
- **`in_payment` invoices** — excluded from the calculation (their payment already appears through direct `done` transactions)

### Visual decorations

`payment_amount` and `payment_status` are color-coded in both form and list views:

| Color | Statuses |
|---|---|
| Green (`success`) | `done` |
| Yellow (`warning`) | `partial`, `pending`, `initiated`, `authorized` |
| Red (`danger`) | `cancelled` |
| Grey (`muted`) | `without` |

### Filters in the order list

Quick filters for all payment statuses: Without payment, Initiated, Pending, Authorized, Done, Cancelled.

### Data migration

When upgrading to version `18.0.1.2.0`, a SQL script automatically populates the `payment_amount` and `payment_status` columns for all existing orders without locking the database.
