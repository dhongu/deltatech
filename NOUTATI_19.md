# Ce e nou în 19.0 — Suita deltatech — module de bază pentru ERP

Sinteză a noutăților față de versiunea 18.0, pe 47 module. Detaliile fiecărui modul sunt în
`<modul>/readme/NOUTATI_19.md`.

## Module noi în 19.0 (13)

- **Câmp Markdown** (`deltatech_markdown_field`) — Editare vizuală pentru câmpurile de text lungi, cu bară de
  instrumente (îngroșat, cursiv, titluri, liste, citate, blocuri de cod, linkuri), în timp ce în baza de date se….
- **Formule în rețeta de fabricație** (`deltatech_mrp_bom_formula`) — Cantitatea unei componente se calculează din
  atributele variantei fabricate, printr-o formulă, în locul repetării aceleiași componente pe câte o linie pentru
  fiecare….
- **Comasare parteneri în masă** (`deltatech_partner_merge`) — Comasează în minute partenerii duplicați pe același CUI,
  în masă.
- **Sincronizare preț în POS** (`deltatech_pos_price_sync`) — Schimbarea prețului ajunge instantaneu în sesiunile POS
  deja deschise.
- **Scor de vizibilitate a produsului pe site** (`deltatech_product_visibility`) — Un scor 0–100 de vizibilitate pentru
  fiecare produs, afișat ca semafor colorat, cu defalcare pe criterii — dintr-o privire se vede cât de complet și de
  găsibil este….
- **Listă de prețuri pe proiect** (`deltatech_project_price_list`) — Listă de prețuri definită la nivel de proiect,
  folosită automat la crearea comenzilor de vânzare din proiect sau din sarcini — managerul de proiect nu mai trebuie
  să….
- **Buton „Creează factură" la achiziții** (`deltatech_purchase_create_bill_button`) — Readuce butonul clasic „Creează
  factură" pe comanda de achiziție.
- **Cereri de ofertă din ofertă de vânzare** (`deltatech_sale_purchase_requisition`) — Buton pe oferta de vânzare care
  generează cereri de ofertă către furnizori din liniile ofertei, cu legătura păstrată înapoi la ofertă.
- **Unități de măsură secundare pe produs** (`deltatech_secondary_uom`) — Factori de conversie specifici fiecărui produs
  între unitatea de bază și o unitate alternativă (după modelul SAP MARM).
- **Cantitate multiplă la regulile de reaprovizionare** (`deltatech_stock_orderpoint_multiple`) — Readuce rotunjirea la
  un multiplu pe regulile de reaprovizionare, câmp pe care Odoo l-a eliminat la trecerea la versiunea 19.0.
- **Terrabit Connect (bază)** (`deltatech_tc`) — Puntea dintre Odoo din cloud și echipamentele din rețeaua locală a
  clientului — casă de marcat, cântar, linie de sortare, PLC, server de etichete — pe care Odoo nu le….
- **Logo după echipa de vânzare** (`deltatech_team_logo`) — Logo diferit în rapoartele PDF (factură, ofertă/comandă,
  aviz de livrare) în funcție de echipa de vânzare a documentului — soluția pentru companiile care operează mai….
- **Transport de configurări între medii** (`deltatech_transport_change`) — Export al modificărilor de configurare și
  transportul lor între medii (dezvoltare → test → producție), urmărite prin git — configurările nu mai sunt reintroduse
  manual….

## Module cu funcționalități noi față de 18.0 (34)

- **Acțiuni de curățare a bazei** (`deltatech_actions`) — Curățările se pornesc și se opresc din Setări.
- **Procese de implementare** (`deltatech_business_process`) — Bibliotecă de procese alimentată din module și din
  depozite git.
- **Document de predare** (`deltatech_business_process_handover_document`) — Filtrare după etapa de implementare,
  aliniată la etapele definibile de utilizator din modulul de procese — documentul de predare acoperă exact etapa
  dorită.
- **Prețurile concurenței** (`deltatech_competitors_price`) — Urmărirea prețurilor concurenței, prin extragerea automată
  a datelor de pe paginile web ale acestora, cu preluare la cerere — comparația de preț se face în Odoo, nu în….
- **Declarație de conformitate** (`deltatech_dc`) — Formatul tipărit al declarației a fost curățat (structură și stil),
  deci documentul trimis clientului arată corect indiferent de lungimea denumirilor.
- **Optimizare imagini** (`deltatech_image_optimize`) — Eliminarea imaginilor de produs duplicate.
- **Facturarea livrărilor** (`deltatech_invoice_picking`) — Filtrarea livrărilor după „facturat" dă rezultate corecte în
  toate combinațiile (facturat/nefacturat, egal/diferit), inclusiv după facturarea în lot — comportament….
- **Readucerea facturii în ciornă** (`deltatech_invoice_to_draft`) — Modulul funcționează pe 19.0, adaptat la modul nou
  în care Odoo 19 organizează grupurile de acces.
- **Acoperirea stocului negativ** (`deltatech_move_negative_stock`) — Modulul funcționează pe 19.0, adaptat la
  modificările Odoo 19 privind mișcările de stoc.
- **Partener generic** (`deltatech_partner_generic`) — Partenerul generic este protejat împotriva modificărilor
  accidentale.
- **Codificare produse** (`deltatech_product_code`) — Verificarea unicității codurilor de bare ține cont de companie,
  deci în bazele multi-companie nu mai raportează fals duplicate între companii diferite.
- **Dimensiuni produs** (`deltatech_product_dimension`) — Modulul este complet aliniat cu versiunea 18.0 — aceleași
  câmpuri, ecrane și traduceri.
- **Linie suplimentară pe achiziție** (`deltatech_purchase_add_extra_line`) — Prețul introdus manual pe linia
  suplimentară nu mai este rescris.
- **Actualizare preț furnizor la recepție** (`deltatech_purchase_price`) — Migrarea datelor pe 19.0 folosește utilitarul
  standard, deci prețurile devenite dependente de companie sunt convertite corect și replicate pe toate companiile din
  bază —….
- **Achiziții și stoc** (`deltatech_purchase_stock`) — Comenzile de achiziție generate de reaprovizionare rămân separate
  de cele create manual de cumpărător — sunt marcate ca atare și nu se mai contopesc cu comenzile manuale….
- **Strategii de depozitare** (`deltatech_putaway_strategy`) — Modulul este declarat Production/Stable, aliniat cu
  versiunea 18.0 — capacitățile de locație și strategia extinsă de depozitare sunt disponibile fără restricții de….
- **Cozi de sarcini** (`deltatech_queue_job`) — Sarcinile eșuate duplicate se anulează automat.
- **Raport materiale de ambalare** (`deltatech_report_packaging`) — Evidența materialelor de ambalare consumate pentru
  produsele facturate: configurare pe produs, urmărire pe liniile de factură și asistent de completare în masă — baza….
- **Rapoarte PRN** (`deltatech_report_prn`) — Punct de extensie pentru tipărirea directă, care permite modulului
  companion Zebra să intercepteze raportul și să îl trimită la imprimantă, cu revenire la descărcarea….
- **Audit apeluri RPC** (`deltatech_rpc_audit`) — Auditarea acoperă și noul punct de acces /json/2.
- **Ultima modificare pe comandă** (`deltatech_sale_activity_report`) — Comportamentul rămâne cel din 18.0, acum
  acoperit de teste automate — se consemnează doar modificările făcute de utilizatori reali, nu cele generate de sistem.
- **Linie suplimentară pe vânzare** (`deltatech_sale_add_extra_line`) — Prețul introdus manual pe linia suplimentară se
  păstrează, în loc să fie readus tăcut la valoarea implicită.
- **Analiza vânzărilor pe cotă de TVA** (`deltatech_sale_analysis_vat`) — Cota de TVA devine filtru și criteriu de
  grupare în Analiza facturilor și în Analiza punctului de vânzare.
- **Comisioane de vânzare** (`deltatech_sale_commission`) — Se aliniază la politica configurabilă de vânzare sub cost
  din verificarea marjei — comisionul se calculează coerent cu regula aleasă de companie.
- **Verificarea marjei la vânzare** (`deltatech_sale_margin`) — Reacția la vânzarea sub cost devine politică de
  companie, aleasă din Setări: blocare (comportamentul de până acum), avertizare sau doar consemnare.
- **Vânzare → achiziție** (`deltatech_sale_purchase`) — Anularea comenzii de vânzare elimină corect toate liniile de
  achiziție generate (atâta timp cât comanda de achiziție e încă ciornă), nu doar o parte dintre ele.
- **Închiderea stocului la dată** (`deltatech_stock_close`) — Modulul este disponibil pe 19.0, la paritate cu versiunea
  18.0 — închiderea operațiunilor de stoc la o dată dată funcționează identic.
- **Inventar (metoda clasică)** (`deltatech_stock_inventory`) — Nota de inventar este vizibilă implicit pe linie.
- **Jurnal de activitate pe livrări** (`deltatech_stock_picking_activity_report`) — Descrierea operațiilor transferului
  nu mai este trunchiată.
- **Categorii publice în magazin** (`deltatech_website_category`) — Modulul este disponibil pe 19.0, cu arbore de
  categorii încărcat la cerere — magazinele cu structuri mari de categorii se deschid rapid, iar ce oferă deja nucleul
  Odoo….
- **Localități pe site** (`deltatech_website_city`) — Lista de localități de la finalizarea comenzii se restrânge la
  cele acceptate de curierul ales, atunci când curierul are catalog propriu de localități.
- **Căutare după cod în magazin** (`deltatech_website_product_code`) — Căutare pe frază exactă pentru codurile care
  conțin spații, plus eliminarea termenilor prea scurți din căutare — rezultate relevante pentru clienții care caută
  după cod….
- **Filtre de atribute în magazin** (`deltatech_website_sale_attribute_filter`) — Starea filtrelor se păstrează la
  reselectare, deci clientul nu mai pierde criteriile alese când modifică un filtru.
- **Optimizarea barei de căutare** (`deltatech_website_searchbar`) — Fără schimbări funcționale față de 18.0: bara de
  căutare trimite mai puține cereri de completare automată, prin întârzierea sugestiilor și lungimea minimă a
  termenului.

## Module de pe 18.0 fără corespondent în 19.0 (56)

Pentru completitudine, în sens invers: module care există pe ramura 18.0 și nu au (încă) un echivalent pe 19.0.

**Retrase deliberat (6)** — marcate obsolete/neinstalabile pe 18.0 sau înlocuite:

- `deltatech_account_edi_ubl_gln` — Deltatech UBL GLN - Obsolete
- `deltatech_print_bf` — Deltatech Print Invoice to ECR - Obsolete
- `deltatech_restricted_access` — Restricted Access Obsolete
- `deltatech_saleorder_type` — Terrabit - Sale Order Type - Obsolete
- `deltatech_select_journal` — Deltatech Select Journal - Obsolete
- `deltatech_stock_date` — Stock Date - Obsolete

**Nemigrate încă (50)** — fără semnal de retragere; ultima modificare pe 18.0 în paranteze:

- `deltatech_account_restrict_date` — Restrict account date (2025-11)
- `deltatech_business_process_documentation` — Business process documentation (2026-07)
- `deltatech_card_payment` — Deltatech Payment Method Card (2026-03)
- `deltatech_cash` — Cash In / Out (2026-03)
- `deltatech_change_uom` — Change Unit of measure (2025-11)
- `deltatech_dummy_queue_job` — Deltatech Dummy Queue Job (2026-03)
- `deltatech_invoice_color` — Deltatech Invoice Color (2025-11)
- `deltatech_invoice_delivery` — Deltatech Invoice Delivery (2025-11)
- `deltatech_invoice_payment` — Invoice Payment (2026-03)
- `deltatech_maintenance` — Maintenance Extension (2026-03)
- `deltatech_mrp_set_delivery` — Deltatech restrict incomplete set deliveries (2026-03)
- `deltatech_packaging` — Packaging (2026-03)
- `deltatech_partner_discount` — Deltatech partner discount (2025-11)
- `deltatech_partner_minimal_aquisition` — Partner Minimal Aquisition (2026-03)
- `deltatech_payment_report` — Deltatech Payment Report (2026-03)
- `deltatech_payment_term_fix` — Payment Term Fix (2026-03)
- `deltatech_payment_term_restrict` — Deltatech Payment Term Restrict (2025-11)
- `deltatech_picking_number` — Picking Number (2025-11)
- `deltatech_picking_split` — Picking Split (2026-03)
- `deltatech_pos_time_interval` — POS Order Time Interval (2026-03)
- `deltatech_price_change` — Price Change (2025-11)
- `deltatech_price_modify_reception` — Price modify at the reception (2026-03)
- `deltatech_pricelist_add_category` — Price List add Category (2025-11)
- `deltatech_pricelist_vat_cost` — Base pricelist on cost with vat (2026-03)
- `deltatech_product_category` — Products Category (2025-11)
- `deltatech_product_margin` — Deltatech Product Margin (2026-07)
- `deltatech_purchase_confirmation_reminder` — Purchase Confirmation Reminder (2026-03)
- `deltatech_purchase_discount` — Deltatch Discount in purchase order line (2026-03)
- `deltatech_purchase_price_history` — Purchase Price History (2025-11)
- `deltatech_purchase_refund` — Refund Purchase (2026-03)
- `deltatech_reccurent_task_activity` — Create activity on recurring task (2025-11)
- `deltatech_replenish` — Deltatech Replenish (2026-03)
- `deltatech_reset_en_names` — Product Reset EN Names (2026-03)
- `deltatech_sale` — Sale Extension (2026-03)
- `deltatech_sale_catalog_website` — Sale Catalog Website Categories & Image Zoom (2026-07)
- `deltatech_sale_followup` — Sale Followup (2026-03)
- `deltatech_sale_transfer` — Sale Prepare Transfer (2026-04)
- `deltatech_stock_analytic` — Deltatech stock move analytic (2026-03)
- `deltatech_stock_sn` — Stock Serial Number (2026-04)
- `deltatech_transfer_product_to_product` — Transfer Product to Product (2025-11)
- `deltatech_utils` — Deltatech Utils (2026-03)
- `deltatech_warehouse` — MRP Warehouse (2026-03)
- `deltatech_warehouse_access` — Warehouse Access (2026-03)
- `deltatech_warranty` — Deltatech Warranty (2026-04)
- `deltatech_website_access_design` — Website web designer access (2025-11)
- `deltatech_website_delivery_address` — eCommerce Delivery Address (2026-03)
- `deltatech_website_floating_widgets` — Website Floating Widgets (2026-05)
- `deltatech_website_sale_wishlist` — eCommerce Wishlist (2026-03)
- `deltatech_website_snippet_attribute_filter` — eCommerce Attribute Filter Snippet (2026-03)
- `deltatech_website_texture_attributes` — eCommerce Attribute Texture (2026-03)
