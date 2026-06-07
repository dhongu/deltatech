## Prepare a batch from purchase/sale orders

1. Go to **Inventory > Warehouse Management > Prepare batch** (menu added by this module).
2. The **Prepare Batch** wizard opens. Fill in:
   - **Partner** — the supplier (purchase mode) or customer (sale mode) whose open
     transfers you want to group.
   - **Responsible** — the user responsible for the batch.
   - **Reference** — optional reference label for the batch.
   - **Mode** — choose *Purchase* (incoming) or *Sale* (outgoing).
   - **Set done qty** — tick to pre-fill done quantities from the product list below;
     leave unticked to keep the demand quantities.
   - **Lines** (visible in Purchase mode) — optional product/quantity list to restrict
     which products are included and at what quantity.
3. Click **Confirm**. The wizard finds all open pickings for the selected partner and
   mode, creates a confirmed batch, assigns availability, and opens the new batch.

Alternatively, from a **Sale Orders** list view select one or more orders and use the
action **Prepare batch** (bound to the sale order list) — the wizard pre-fills the
customer and sets mode to *Sale*.

## Add a single transfer to a batch

1. Open any transfer (**Inventory > Transfers**) that is not yet in a batch.
2. Click the **Add to batch** button (visible when the transfer has no batch assigned
   and is not in state Done/Cancelled).
3. The standard Odoo "Add to batch" dialog opens; select or create the target batch
   and confirm.

## Validate a batch (empty-picking handling)

1. Open the batch (**Inventory > Batch Transfers**).
2. Process the transfers normally (scan barcodes or fill in done quantities).
3. Click **Validate**. The module inspects each picking:
   - Pickings where no move line has a done quantity > 0 are treated according to the
     `deltatech_batch_keep_pickings` parameter (see CONFIGURE).
   - Non-empty pickings proceed to validation as usual.

## Print the Deliveries batch report

1. Open a batch transfer.
2. Click **Print > Deliveries** (report bound to batch transfers).
3. A PDF is generated containing the standard delivery document for each picking in
   the batch.

## Reading the batch form

The batch form shows three extra fields added by this module:

- **Reference** — free-text identifier, visible next to the picking type.
- **Note** — additional notes for the batch.
- **Direction** — read-only field showing *Incoming* or *Outgoing*.
- **Received** tab — available on incoming batches; lists only move lines that have a
  done quantity > 0 (shown in bold); zero-quantity lines appear muted.
