Features:
 - A force date required setting can be configured in the picking type. The effective date will be required for pickings
 - The picking effective date must be set by the user
 - Due to date restrictions, only one picking can be validated at a time
 - All the stock moves will have the picking's effective date.
 - Can restrict stock move dates to current and previous month by setting the system parameter "restrict_stock_move_date_last_months" to a non-zero value. The account lock date is also taken into consideration
 - Can restrict future stock move date by setting the system parameter "restrict_stock_move_date_future" to a non-zero value (default). Date restrictions must be active (restrict_stock_move_date_last_months)
