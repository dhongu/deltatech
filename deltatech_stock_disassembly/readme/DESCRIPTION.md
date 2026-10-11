# Free Disassembly

## Overview

A **disassembly report** takes one product out of stock and brings in the products obtained
from it, without a bill of materials or a manufacturing order. The cost of the disassembled
product is split over the resulting products, and the module posts one journal entry for the
whole report.

## Features

- **Numbered document**, draft → done (`PVD/<year>/<number>`), with the committee, the reason
  and a printable PDF report with signatures.
- **Disassembled product** taken from an internal location, with its lot or serial number, at
  its **actual cost**: average cost, FIFO layers or lot cost, as computed by the stock valuation.
  Only the own stock of the company can be disassembled, and never more than is available.
- **Resulting products** entered freely, each with its quantity, unit, destination location and
  lot (an existing one or a new lot name, created at validation).
- **Cost allocation** by quantity, by reference price × quantity, by percentages or by fixed
  values. Lines with a fixed value (for example recoverable waste at its net realisable value)
  are deducted first; rounding differences go to the last line. The resulting moves enter the
  stock exactly at their allocated value (average cost is updated, FIFO and lot layers are
  created).
- **Loss lines** (technological loss, non-recoverable waste) sent to a loss location: within the
  technological norm they get no value (the cost stays in the resulting products); above the norm
  they must get a value and are booked as an expense, with a reminder in the chatter and on the PDF
  about the non-deductible expense and the input VAT adjustment.
- **One journal entry per report** in the stock journal, at the date of the report, instead of one
  entry per stock move. The lines carry the product and the quantity, and every stock move of the
  report is linked to the entry.
- **Romanian chart of accounts** (fiscal country Romania), by synthetic account:
  - stock to stock entry on the same synthetic account (371 → 371, 302 → 302) and where the chart
    provides the correspondence: own products used as materials or sold as goods (341 → 301/302,
    345 → 301/302/303/371, 347 → 301/302/371) and materials sold as goods (30x → 371); the lines on
    the same account are not netted, for the audit trail;
  - resulting products on 34x (for example residual products, 346) enter through 711: the
    disassembled product leaves through its expense account (60x/607, or 711 for own products);
  - goods turned into materials (371 → 30x) and materials of another kind (301 ↔ 302 ↔ 303) only
    when the company allows it in the settings, as part of its accounting policy;
  - any other pair of accounts (for example residual products 346 into materials or goods) is
    refused before the stock is moved.
- The disassembled product and the resulting products must have the same valuation (automated or
  manual), so that the journal entry is complete.
- Works with the Romanian localization of stock accounting (accounts per location are used), and
  without it.
