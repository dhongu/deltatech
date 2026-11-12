Fleet locations and routes have no geographic position, so they cannot be matched to a map or a tracking system. This module adds latitude and longitude to them as plain stored numbers.

- **Location coordinates**: The location form shows *Latitude* and *Longitude* after the *Type* field, with six decimals each.
- **Route coordinates**: The route form shows *Latitude from*, *Longitude from*, *Latitude to* and *Longitude to* next to the *From* and *To* locations. They are read from those locations and cannot be edited on the route, so a corrected location updates every route that uses it.
- **Fields without screens**: A *Radius* (default 1.0) on locations and a latitude and longitude on vehicle location entries are stored, but no form or list shows them.
- **Get location button**: A *Get location* button appears on the vehicle form. It has no group restriction, but its method is empty, so clicking it changes nothing.

The module depends on *Fleet Map Sheets & Fuel* (`deltatech_fleet`) and adds no menus, settings or access rights: locations and routes stay available to fleet administrators, as defined there. It draws no map, looks up no addresses and sends no data to an external service.
