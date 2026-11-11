Phone numbers typed on a website checkout come in many formats, and wrong ones are found only when someone calls. This module checks the number when the customer submits an address and rewrites it in the international format.

- **Trimmed input**: Spaces before and after the phone number are removed before the standard checks run.
- **International format**: If the standard checks pass, the number is read for the country selected in the address and rewritten in the international format, so a local number gets the country prefix.
- **Invalid numbers**: A number that cannot be read for that country is reported as invalid, with the message *The phone number is not valid:* followed by the reason.
- **Any address type**: The check applies to the phone number of every address submitted this way, whatever its type.

The module depends on *eCommerce* (`website_sale`) and `phone_validation`, and needs the Python library `phonenumbers` on the server. It overrides only the address validation of the website checkout and acts only on the phone field.
