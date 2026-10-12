# Free Disassembly - Bill of Materials

## Overview

Bridge between **Free Disassembly** and **Manufacturing**, installed automatically when both are
present. The resulting products of a disassembly report can be filled in from a bill of materials,
instead of being entered one by one; the report stays free and does not need a manufacturing order.

## Features

- **Bill of Materials** field on the disassembly report, proposed from the disassembled product
  (normal bills of materials, matching the product or its template), and changeable.
- **Load from BoM** button (draft only): replaces the product lines by the components of the bill of
  materials, for the disassembled quantity converted to the unit of the bill of materials. Kits are
  exploded down to their components, services are skipped and the loss lines are kept.
- The loaded lines can then be changed, removed or completed freely; the cost allocation and the
  accounting are those of the disassembly report.
