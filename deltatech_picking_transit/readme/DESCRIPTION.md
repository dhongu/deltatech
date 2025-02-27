Features:

- On the stock picking type form you can add "next operation"
- when you make an internal transfer with a picking type that has the "next operation" set, the system gives you the
  option to make the transfer a 2 step one with the button "create transfer"
- the button will create another transfer from the transit location to the location selected on the wizard with the same
  move lines
- after the second transfer is created, you will not be able to modify the move lines of the initial transfer
- v17.0.0.0.9: added the option for the second transfer to be created automatically without the need of the wizard
  - on the stock picking type there will be a check box "Auto Second Transfer" this check box will apper only if the
    "Two Step Transfer Use" is set to Delivery
  - if the check box is set, when validating the first transfer, the system will try to find the Reception location
    based on the partner of the transfer (use the contact associated to the second warehouse)
  - if the "Source Document" is set on the picking the system will **not** automatically create the second transfer
