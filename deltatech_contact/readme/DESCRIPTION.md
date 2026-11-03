Extends the standard Odoo Contacts module with personal data for individual
contacts: the Romanian CNP (Personal Numeric Code) with checksum validation,
identity card details, birthdate, gender and means of transport.

**Personal Data tab.** On a contact with the address type *Contact* that is not
a company (in Odoo 20 a contact without a parent company is a company when it
has a VAT number), the tab **Personal Data** groups the identity card (**Card ID
Number**: series and number; **Card ID Issued**: issuing authority and date) and
the **CNP**, **Birthdate** and **Gender**. The same fields are on the form of a
contact added from a company and on the quick-create form.

**Birthdate and gender from the CNP.** When a CNP is entered, the birthdate is
taken from digits 2 to 7 and the gender from the first digit. Changing the
birthdate rewrites the date digits of the CNP and recomputes its check digit.

**CNP validation.** The CNP must have 13 digits and a valid check digit. Saving
an existing contact with an invalid CNP stops with the message *CNP invalid*. On
a new contact, created from the form or by import, an invalid CNP is cleared on
save, without a message. An empty CNP is accepted.

**Means of transport.** The field **Mean Transport** (for example the plate
number of a delegate's car) is shown under *Reference* in the **Sales &
Purchase** tab of a contact that is not a company.

**Search filters.** In **Contacts > Contacts**, the search gets the filters
**Persons** and **Companies**, which show only contacts without a parent
company (Odoo 20 no longer has them as standard), and **Delivery** and
**Invoice** for addresses of these types.

**Contacts tab.** On a contact that belongs to a company, the standard
**Contacts** tab is hidden.

**Contact name without the company.** When the system parameter
`contact.get_name_only` is set, contacts of type *Contact* are shown by their
own name, without the name of their company.

**Display name options for developers.** The context keys `show_phone`,
`show_category` and `address_inline` add the phone number or the tags to the
contact name in relational fields, or put the name and address on one line.

## Limitations

- Because the birthdate is filled from the CNP, and the CNP is then rebuilt from
  the birthdate, a CNP typed in the form with a wrong check digit gets the
  correct check digit without any message. A CNP of 12 digits is completed
  with a check digit the same way. Compare the CNP with the identity
  card.
- First digits 1 and 2 give a birth year in the 1900s, any other digit the
  2000s; the gender is male only for the first digits 1 and 5.
- A CNP of 8 to 11 characters, or one whose digits 2 to 7 are not a valid date,
  makes the form fail with a technical error instead of a validation message.
