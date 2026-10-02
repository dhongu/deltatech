Work with transfers as usual. When a user validates a transfer, the module checks every
line that takes stock out of an internal location:

- if enough stock is left, the transfer is validated normally;
- if the location would go below zero, the validation stops with a message such as
  *"You have chosen to avoid negative stock. -2 pieces of Desk Combination are
  remaining in location Stock."*

The user can then lower the quantities, pick from another location or lot, or correct
the stock with an inventory adjustment first. A stock that is already wrong can always
be brought back with an inventory adjustment.
