1. Create the team group (*Settings > Users & Companies > Groups*, in developer mode) and add its
   members in the **Users** tab. They need the Inventory **User** right and access to the company of
   the transfers.

   ![Form of the group Echipa vopsele, Users tab: the direct members Ana Popescu and Mihai Ionescu (1)](static/description/en/01_grup_echipa_membri.png)

2. Optionally, add the team group to the **Implied Groups** of another group, in its **Inherited** tab.
   The members of that group get the team group too and are candidates like the direct members.

   ![Form of the group Șefi de tură, Inherited tab: Echipa vopsele in Implied Groups (1)](static/description/en/02_grup_sefi_include_echipa.png)

3. Set the team on the product category (*Inventory > Configuration > Products > Product
   Categories*), in the **User Group** field. The groups of the category and of up to three parent
   levels are combined: a subcategory group does not replace the parent group.

   ![Product category Vopsele with User Group set to Echipa vopsele (1)](static/description/en/03_categorie_grup_utilizatori.png)

4. Open a transfers list (for example *Inventory > Operations > Transfers > Deliveries*), show the
   optional **Responsible** column, select the **Ready** transfers without a responsible and click
   **Responsible**. The button is shown only to Inventory **Administrator** users, after a selection.

   ![Deliveries list with three Ready transfers selected, an empty Responsible column (2) and the Responsible button (1)](static/description/en/04_transferuri_buton_responsabil.png)

5. Each transfer gets a member of the team: first a member without Ready transfers in that company,
   otherwise the one with the fewest. Transfers that are not Ready or already have a responsible are
   left as they are.

   ![The same list after the click: one delivery each for Ana Popescu, Mihai Ionescu and Elena Dumitru (1)](static/description/en/05_responsabili_alocati.png)
