**Note:** on 19.0 the sending does not work yet (see *Limitations* in the description). The steps
below show the configuration and the current behaviour.

1. In **Sales > Configuration > Settings**, section **Invoicing**, tick **Email feedback after sale**.
   The **Email Template Request Feedback** field shows the module's template,
   *Invoice: request feedback*. The option is stored but not used by the sending.

   ![Sales settings, Invoicing section: Email feedback after sale is ticked and Email Template Request Feedback is set to Invoice: request feedback](static/description/en/01_setari_feedback.png)

2. The delay after the invoice date is the `sale.days_request_feedback` system parameter
   (**Settings > Technical > Parameters > System Parameters**, developer mode), 3 days by default.

   ![System parameter form with Key sale.days_request_feedback and Value 3](static/description/en/02_parametru_zile.png)

3. The **Request Feedback** scheduled action (**Settings > Technical > Automation > Scheduled
   Actions**) runs daily and is inactive at install. Once active, it sends the e-mail for the
   customer invoices dated that many days ago, whatever their state.

   ![Request Feedback scheduled action on Journal Entry, run daily by OdooBot, with the Active toggle off and model.cron_request_feedback() in the Code tab](static/description/en/03_actiune_programata.png)

4. To send it by hand, open a customer invoice, click the **Actions** gear and choose
   **Request feedback** (it also works on several invoices selected in the list).

   ![Posted customer invoice INV/2026/00001 for Magazin Exemplu SRL with the Actions menu open and Request feedback highlighted](static/description/en/04_meniu_actiuni_factura.png)

5. On 19.0 this stops with the **Oops!** error dialog and no e-mail is sent: the code still calls
   Odoo functions that no longer exist.

   ![The same invoice with the Oops! error dialog: Something went wrong, See technical details and Close](static/description/en/05_eroare_trimitere.png)

6. The e-mail is the *Invoice: request feedback* template (**Settings > Technical > Email >
   Templates**): per invoice line, the product image, a link to the product page, the quantity and
   the three rating links. Its subject, sender, recipient and language still use the old `${...}`
   syntax. Previewing it creates an empty rating on each product shown.

   ![Invoice: request feedback template on Journal Entry, with the subject in the old ${...} syntax and the body Dear, Please take a moment to rate our products](static/description/en/06_sablon_email.png)
