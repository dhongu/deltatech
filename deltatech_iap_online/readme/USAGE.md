The screens of this module are for administrators, in *Settings > Terrabit Credits*, without the
developer mode. Install it together with a Terrabit service module (e.g.
`l10n_ro_anaf_partner_online`), which creates the service record.

1. **Open the menu**: in *Settings*, the **Terrabit Credits** menu (1) has two entries (2):
   **Services and Credits** and **Credit Usage**. In developer mode, the same services and the full
   list of requests are also under *Settings > Technical > Terrabit Services*.

   ![Settings app with the Terrabit Credits menu open in the top bar (1) and its dropdown with Services and Credits and Credit Usage (2)](static/description/en/01_meniu_servicii.png)

2. **Check the service**: *Terrabit Credits > Services and Credits* lists one line per installed
   service, with its **Service Code** and **Credits Left**.

   ![Terrabit Services list with two lines; the TEST ANAF Partner Data line, with the code anaf_partner_online and 4.860 credits left, is highlighted](static/description/en/02_lista_servicii.png)

3. **Activate the service**: open it and click **Activate**, the only button of a service not yet
   active. The database is registered at the Terrabit server and an activation request (`register`)
   appears in *Requests*; a few seconds later the account token comes back by itself, with the trial
   credits. Nothing to copy or paste.

   ![Form of a TEST ANAF Partner Data service not yet active: only the Activate button in the header, highlighted, then Service Code anaf_partner_online, the Server URL and Credits Left at 0.000](static/description/en/03_activare_serviciu.png)

4. **Use the active service**: right after the click, the header shows **Activate Again**,
   **Refresh Credits** and **Buy Credits**. Check in *Requests* that the activation is *Done* before
   using them; if it is in error, click **Activate Again**. The **Credit Usage** button, at the top,
   opens the credit usage of the service (step 11).

   ![Form of the active TEST ANAF Partner Data service: the Credit Usage button at the top; Activate Again, Refresh Credits (1) and Buy Credits (2) in the header, then Service Code, Server URL and Credits Left 4.860 (3)](static/description/en/04_formular_serviciu.png)

5. **Refresh the credits**: **Refresh Credits** asks the server for the credits left; a notification
   confirms the request and **Credits Left** is updated in a few seconds. The credits are also
   updated with every answer of the service.

   ![TEST ANAF Partner Data service form after Refresh Credits, with the Terrabit notification highlighted: Request sent: the credits are updated in a few seconds](static/description/en/05_actualizare_credite.png)

6. **Buy credits**: **Buy Credits** opens, in a new browser tab, the credit page of your account on
   the Terrabit server. After the purchase, click **Refresh Credits**.

   ![Credit page of the Terrabit server: Buy credits for ANAF Partner (Odoo Online) and the Your account box with the credits of the account](static/description/en/06_cumparare_credite.png)

7. **Follow the requests**: in developer mode, *Settings > Technical > Terrabit Services > Requests*
   lists all the requests, newest first, with their **Request Type**, **Status**, **Error** and
   **Credits Used**. Requests in error are red, requests still
   waiting are blue; the **Errors** and **Waiting** filters narrow the list. A request without
   answer 10 minutes after its creation is sent once more, automatically.

   ![Terrabit Requests list, newest first, with a credit (balance) request and partner lookup (request) requests: the lines with the Error status are red and their Invalid CUI errors are highlighted (1, 2); the last column, Credits Used, shows 0.020 for the answered requests and 0.000 for those in error](static/description/en/07_lista_cereri.png)

8. **Read a request in error**: open it to see the service, the input, the document it was sent
   from (**Document Model**, **Document ID**), the **Status**, the **Error**, **Credits Used** and
   **Credits Left After**. A request refused by the server uses no credits. Fix the data on that
   document and send the request again from the service module.

   ![Read-only form of a TEST ANAF Partner Data request with Input 1234567 on res.partner 3: Status Error (1), Error Invalid CUI (2) and Credits Used 0.000 (3) highlighted, then Credits Left After 4.920](static/description/en/08_cerere_eroare.png)

9. **Check the credit usage**: *Settings > Terrabit Credits > Credit Usage* lists, with the
   **Charged** filter set by default (1), each answer the server charged, with its **Credits Used**
   and the total at the bottom of the column (2); 1 credit = 1 EUR. Activations, credit refreshes
   and refused requests cost nothing and are not listed. Filter by **Date** or **Service**, or group
   by **Service** or **Month**; the optional **Credits Left After** column shows the credits left
   after each answer. The server sends the cost with each answer: requests answered before version
   19.0.1.1.0 have no cost.

   ![Credit Usage list with the Charged filter highlighted (1): 17 requests of the TEST ANAF Partner Data service from September to November 2026, each with 0.020 credits used, and the total 0.340 at the bottom of the column highlighted (2)](static/description/en/09_consum_credite_lista.png)

10. **See the usage by month**: switch to the **Graph** or **Pivot** view (top right). The graph
    shows the credits used per month, one color per service; the pivot has the months in rows, the
    services in columns and the totals.

    ![Credit Usage graph with the Charged filter: bars for September, October and November 2026 for the TEST ANAF Partner Data service, with 0.08, 0.14 and 0.12 credits](static/description/en/10_consum_credite_grafic.png)

    ![Credit Usage pivot with the Charged filter: September, October and November 2026 in rows, the TEST ANAF Partner Data service in column, with Credits Used 0.08, 0.14, 0.12 and the total 0.34](static/description/en/11_consum_credite_pivot.png)

11. **Credit usage of one service**: on the service form, the **Credit Usage** button opens the same
    list with the **Service** and **Charged** filters, with the total, the graph and the pivot.

    ![Form of the TEST ANAF Partner Data service with the Credit Usage button at the top highlighted](static/description/en/12_buton_consum_credite.png)

Only administrators see the *Terrabit Credits* menu and read the services (account token) and the
requests (callback URL); other users create requests from the buttons of the service modules,
without reading them.
