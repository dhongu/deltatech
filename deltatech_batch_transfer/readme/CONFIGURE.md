## System parameter: deltatech_batch_keep_pickings

This parameter controls how empty pickings (all done quantities = 0) are handled when
a batch is validated.

**Location:** Settings > Technical > Parameters > System Parameters

| Parameter key | Value | Effect |
|---|---|---|
| `deltatech_batch_keep_pickings` | *(not present / absent)* | Empty pickings are **removed** from the batch on validate. They can be manually added to another batch. **(recommended)** |
| `deltatech_batch_keep_pickings` | `True` | Empty pickings are **kept** in the batch but skipped during validation; they remain for later processing. Not recommended when using the barcode interface. |

**To configure:**

1. Go to **Settings > Technical > Parameters > System Parameters**.
2. Search for `deltatech_batch_keep_pickings`.
   - If the parameter does not exist (default), empty pickings are removed on validate —
     no action needed.
   - To keep empty pickings in the batch, click **Create**, set the key to
     `deltatech_batch_keep_pickings` and the value to `True`.
3. Save. The change takes effect immediately on the next batch validation.
