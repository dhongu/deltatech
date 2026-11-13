The screens of this module are for administrators, in developer mode (*Settings > Technical*).
Install it together with a Terrabit service module (e.g. `l10n_ro_anaf_partner_online`), which
creates the service record.

1. **Open the menu**: activate the developer mode, then go to *Settings > Technical > Terrabit
   Services*. It has two entries: **Services** and **Requests**.

   ![Technical menu of Settings scrolled to the Terrabit Services section, with the Services and Requests entries highlighted](static/description/en/01_meniu_servicii.png)

2. **Check the service**: *Terrabit Services > Services* lists one line per installed service, with
   its **Service Code** and **Credits Left**.

   ![Terrabit Services list with one line: the ANAF Partner Data service, the code anaf_partner_online and the credits left](static/description/en/02_lista_servicii.png)

3. **Activate the service**: open it and click **Activate**, the only button of a service not yet
   active. The database is registered at the Terrabit server and an activation request (`register`)
   appears in *Requests*; a few seconds later the account token comes back by itself, with the trial
   credits. Nothing to copy or paste.

   ![Form of the ANAF Partner Data service not yet active: only the Activate button in the header, highlighted (1), then Service Code anaf_partner_online, the Server URL and Credits Left at 0.00](static/description/en/03_activare_serviciu.png)

4. **Use the active service**: right after the click, the header shows **Activate Again**,
   **Refresh Credits** and **Buy Credits**. Check in *Requests* that the activation is *Done* before
   using them; if it is in error, click **Activate Again**.

   ![Form of the active ANAF Partner Data service: Activate Again, Refresh Credits (1) and Buy Credits (2) in the header, then Service Code, Server URL and Credits Left (3)](static/description/en/04_formular_serviciu.png)

5. **Refresh the credits**: **Refresh Credits** asks the server for the credits left; a notification
   confirms the request and **Credits Left** is updated in a few seconds. The credits are also
   updated with every answer of the service.

   ![Service form after Refresh Credits, with the Terrabit notification: Request sent: the credits are updated in a few seconds](static/description/en/05_actualizare_credite.png)

6. **Buy credits**: **Buy Credits** opens, in a new browser tab, the credit page of your account on
   the Terrabit server. After the purchase, click **Refresh Credits**.

   ![Credit page of the Terrabit server: Buy credits for ANAF Partner (Odoo Online) and the Your account box with the credits of the account](static/description/en/06_cumparare_credite.png)

7. **Follow the requests**: *Terrabit Services > Requests* lists the requests, newest first, with
   their **Request Type**, **Status** and **Error**. Requests in error are red, requests still
   waiting are blue; the **Errors** and **Waiting** filters narrow the list. A request without
   answer 10 minutes after its creation is sent once more, automatically.

   ![Terrabit Requests list, newest first, with credit (balance) and partner lookup (request) requests: the lines with the Error status are red and their Invalid CUI errors are highlighted](static/description/en/07_lista_cereri.png)

8. **Read a request in error**: open it to see the service, the input, the document it was sent
   from (**Document Model**, **Document ID**), the **Status** and the **Error**. Fix the data on that
   document and send the request again from the service module.

   ![Read-only form of an ANAF Partner Data request with Input 1234567 on res.partner 7: Status Error (1) and Error Invalid CUI (2) highlighted](static/description/en/08_cerere_eroare.png)

Only administrators read the services (account token) and the requests (callback URL); other
users create requests from the buttons of the service modules, without reading them.
