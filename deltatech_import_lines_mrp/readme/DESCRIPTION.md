Adds an **Import Components** button on draft and confirmed
manufacturing orders that adds component moves from a file with the
wizard of `deltatech_import_lines`.

- Each row becomes a component move, prepared as a component added by
  hand (locations, operation, procurement method).
- On a confirmed order, the new components are confirmed.
- The product to produce cannot be imported as its own component.

Installed automatically when both Manufacturing and
`deltatech_import_lines` are installed.
