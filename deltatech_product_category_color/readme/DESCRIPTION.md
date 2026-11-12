In a busy warehouse, operators want to see at a glance what kind of goods a transfer holds. This module gives every product category a color and shows the categories of each transfer as colored tags on its Kanban card.

- **Category color**: The product category form gets a color picker, labeled *Color Index*. A new category starts with a random color index between 1 and 11.
- **Colored tags on transfers**: Each card of the transfers Kanban view shows, after the state, one tag for each category of the products in the transfer, in the color of the category.
- **Taken from the move lines**: The categories come from the move lines of the transfer, not from its stock moves, so a product with no move line yet, for example one that is not reserved, adds no tag.
- **Computed, not stored**: The tags are computed when the Kanban view is loaded and are not stored. A changed color applies to every card.

The module depends on *Inventory* (`stock`) and `product`. It changes only the Kanban view of transfers: the list and the form of a transfer stay as they are. The color is a display setting and has no effect on stock or accounting.
