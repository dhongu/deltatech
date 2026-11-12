Phone numbers typed on a website checkout come in many formats, and wrong ones are found only when someone calls. This module checks the number when the customer submits an address at checkout or the details form of the customer portal, and rewrites it in the international format.

- **Trimmed input**: Spaces before and after the phone number are removed before the standard checks run.
- **International format**: The number is read for the country selected in the form and rewritten in the international format, so a local number gets the country prefix. At checkout, this is skipped when the standard checks already flag the number.
- **Invalid numbers**: A number that cannot be read for that country is reported as invalid. The checkout shows the message *The phone number is not valid:* followed by the reason, and the portal shows the reason alone.
- **Any address type**: The check applies to the phone number of every address submitted at checkout, whatever its type.

The module depends on *eCommerce* (`website_sale`) and `phone_validation`, and needs the Python library `phonenumbers` on the server. It overrides the address validation of the website checkout and the validation of the customer portal details form, and acts only on the phone field.
