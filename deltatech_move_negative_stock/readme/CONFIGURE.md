1. Optionally, create an internal operation type for the replenishment, in
   *Inventory > Configuration > Operation Types*, with the warehouse stock as **Default Source
   Location** and the location to refill (for example a showroom) as **Default Destination
   Location**. The transfers then open with the right locations already set.

![](static/description/op-type.png)

2. For the daily email, open *Inventory > Configuration > Locations*, choose an internal
   location and set its **Manager**. Locations without a manager are skipped.

3. The **Send negative stock** scheduled action runs once a day. Its frequency can be changed among the
   scheduled actions, under *Settings > Technical* (developer mode).
