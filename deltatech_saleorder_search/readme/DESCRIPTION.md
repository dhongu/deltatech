Finds sales orders when the only thing you know about the customer is an e-mail
address or a phone number.

**Search by e-mail.** The search bar of quotations and sales orders gets the
option **Search E-mail for: ...**, which returns the orders whose customer has an
e-mail address containing the typed text.

**Search by phone.** The option **Search Phone for: ...** does the same with the
customer's phone number. The text is matched as typed, so enter the number in
the format in which it is stored on the contact.

Both options work in **Sales > Orders > Quotations** and
**Sales > Orders > Orders**, and in every other list of sales orders that uses
the standard search view. Nothing needs to be configured.

The search looks at the e-mail and phone of the contact set as *Customer* on
the order, not at the other contacts of the same company.

Odoo Online
===========

The module contains no Python code, only a search view extension. Besides Odoo.sh and
on-premise installations, it can be used on Odoo Online (Custom plan): download the zip and load
it from **Apps > Import Module**.
