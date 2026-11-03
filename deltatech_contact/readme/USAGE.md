The module has no settings: the **Personal Data** tab appears on every contact of type **Person**
with the address type **Contact**.

1. **Fill in the personal data** — **Contacts → Contacts**, open a person and go to the **Personal
   Data** tab. Under **Identity Card**, fill in the series and number (**Card ID Number**) and the
   issuing authority and date (**Card ID Issued**); under **Other Information**, the **CNP**, the
   **Birthdate** and the **Gender**. On a person linked to a company, the standard **Contacts** tab is
   hidden.

   ![Personal Data tab of Andrei Popescu: ID series PH (1), issued by SPCLEP Ploiești (2), CNP (3), Birthdate (4) and Gender Male (5)](static/description/en/01_contact_date_personale.png)

2. **Let the CNP fill in the birthdate and gender** — on a new contact, choose **Person**, then type
   the CNP in the **Personal Data** tab. The birthdate comes from digits 2–7 and the gender from the
   first digit (1 or 5 = Male). Changing the birthdate rewrites the CNP with the new date and a
   recomputed check digit. The check digit is also corrected silently when you type a CNP with a
   wrong last digit, so compare the CNP with the identity card.

   ![New person Maria Ionescu: CNP 2900315400018 (1), Birthdate Mar 15, 1990 (2) and Gender Female (3) filled in from the CNP](static/description/en/02_cnp_completare_automata.png)

3. **Invalid CNP** — saving an existing contact whose CNP does not have 13 digits or a valid check
   digit stops with **Validation Error — CNP invalid**. On a new contact, or on import, an invalid
   CNP is cleared on save without a message.

   ![Validation Error dialog with the message CNP invalid (1), after saving a contact with the CNP 1850101](static/description/en/03_cnp_invalid.png)

4. **Means of transport** — in the **Sales & Purchase** tab of a person, group **Misc**, the **Mean
   Transport** field holds, for example, the plate number of the delegate's car.

   ![Sales & Purchase tab: Mean Transport PH-10-APR (1) under Reference](static/description/en/04_mijloc_transport.png)

5. **Delivery and invoice addresses** — in the contacts search, the **Delivery** and **Invoice**
   filters list the delivery and invoice addresses. The standard **Persons** and **Companies**
   filters show only contacts without a parent company.

   ![Search menu of the contacts list: the Delivery (1) and Invoice (2) filters under Persons and Companies](static/description/en/05_filtre_livrare_facturare.png)
