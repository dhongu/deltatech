No configuration is required; the extra validation is applied automatically wherever a customer enters a VAT number.

- **Website checkout** and the **customer portal** (My Account > Details) both validate the VAT number before saving the address.
- Whitespace around VAT, email and phone is trimmed automatically.
- If the billing country is Romania, the VAT number is checked against **ANAF**; when a match is found, the company name, street, city and county are filled in automatically from the ANAF record, and the address is flagged as a company if ANAF reports it as such. If ANAF has no valid record for the number, the address form is rejected with an explicit error.
- If the VAT, email or phone already belongs to another (top-level) partner, the address is rejected with an error stating that the value is already in use, preventing duplicate customer records.
