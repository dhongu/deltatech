1. Go to *Sales > Orders > Quotations*, remove the *My Quotations* filter if you also want to see your
   colleagues' quotations, and tick two or more quotations of the same customer. Open the *Actions*
   menu and choose *Merge orders*.

   ![Quotations list with three quotations of the customer Agro Prod SRL ticked and the Actions menu open on the Merge orders entry](static/description/en/01_selectie_oferte.png)

2. Choose where to merge (*The oldest selected quotation*, *A selected quotation* or *A new quotation*)
   and how to treat the lines (*Add up identical lines* or *Keep all lines*). Tick *Add a Section per
   Quotation* to add a section with the number of each merged quotation before the lines copied from it.
   Lines that are added up into an existing line keep no trace of their origin. If the salespersons or
   sales teams differ, a warning tells you that the target quotation's value is kept.

   ![Merge orders window with the warning about a different salesperson, the Merge Into and Lines options and the Add a Section per Quotation box ticked](static/description/en/02_wizard_unire.png)

3. Click *Merge*. If the quotations differ in an important way (for example the customer), a message
   explains why and nothing is changed.

   ![Invalid Operation message: the quotations cannot be merged, Customer is different, listing S00004 Terra Construct SRL and S00001 Agro Prod SRL](static/description/en/03_blocaj_client_diferit.png)

4. Otherwise the target quotation opens with the merged lines.

   ![Target quotation with the added-up lines Șurub M8 30 and Piuliță M8 10, followed by a section per merged quotation](static/description/en/04_oferta_unita.png)

   On the *Other Info* tab, *Merged From* lists the cancelled quotations, and *Customer Reference* and
   *Source Document* gather the values of all the merged quotations.

   ![Other Info tab of the target quotation with the Customer Reference PO-1058, PO-1041 and the Merged From field](static/description/en/05_date_pe_oferta_tinta.png)

5. The other quotations are cancelled, not deleted. Each shows *Merged Into* on the *Other Info* tab and
   a note in the chatter.

   ![Cancelled quotation with the Merged Into field pointing to the target quotation and the chatter note Merged into S00001](static/description/en/06_oferta_anulata.png)

When identical lines are added up, the unit price may be recomputed by the pricelist for the new
quantity (quantity breaks).
