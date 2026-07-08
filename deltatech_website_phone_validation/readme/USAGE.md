No configuration is needed. Once installed:

- On the eCommerce checkout address form and on the Customer Portal "My Account" details form, the phone number entered by the visitor is validated and reformatted (using the country selected on the address) as soon as the form is submitted.
- If the phone number is not a valid number for the selected country, the field is flagged as invalid and an error message ("The phone number is not valid: ...") is shown, blocking the submission until it is corrected.
- Requires the `phonenumbers` Python library to be installed on the server (declared as an external dependency of this module).
