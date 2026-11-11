Shop staff often need to find the point of sale orders that contain a given item. This module adds a *Product* option to the search of POS orders, so an order can be found by what was sold.

- **Product search option**: Typing in the search box of the POS orders offers a new *Product* option, placed right after the partner option.
- **Search on order lines**: The option lists the orders that have at least one line whose product matches the typed text. The match is partial and ignores upper and lower case.
- **Search view only**: The module changes nothing but this search view. It has no Python code, no new fields, no menus and no access groups.

The module depends on *Point of Sale* (`point_of_sale`) and extends its standard POS order search view, so it applies wherever that view is used. It does not add a product column to the list or to any report, and it has no settings.
