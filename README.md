
Deltatech
=================================


deltatech
=========
Modul generic, nu face ceva deosebit.



deltatech_account
=================
- permite dezactivarea de jurnale
- adauga grupul pentru butoane din dreapta sus in facturi



deltatech_account_followup
==========================
- permite blocarea partenerului, cu mesaj de blocare



deltatech_alternative
=====================
- permite definirea unui catalog de produse pentru un numar foarte mare de produse care uzual nu se folosesc
- la cautarea dupa un cod din catalog, sistemul genereaza automat un produs (product.product), copie dupa cel din catalog
- se defineste modelul product_alternative
- se poate cauta un produs dupa alternativa
- in product.template sunt definite campurile:
	- alternative_code - concatenarea tuturor codurilor alternative
	- alternative_ids - lista de produse alternative
	- used_for - la ce este utilizat produsul (text)



deltatech_alternative_inv
=========================
- afiseaza codurile alternative in factura



deltatech_alternative_website
=============================
- cautare produs dupa cod echivalent in website
- afisare imagini produse in magazinul virtual cu watermark
- adauga categoriile afisate in website la catalogul de produse



deltatech_bank_statement
========================
- adauga in liniile extrasului de banca, la referinta, numarul facturii care a fost reconciliata



deltatech_cash_statement
========================
- actualizare automata a soldurilor de inceput si sfarsit la registru de casa (wizard)



deltatech_config_vat
====================
- la modificarea TVA-ului implicit, se modifica TVA-urile la toate produsele si la toate comenzile deschise
- se recomanda dezinstalarea modulului dupa schimbarea TVA-ului



deltatech_contact
=================
- adaugare campuri suplimentare in datele de contact: data nasterii, CNP, carte de identitate, mijloc de transport, daca este departament
- este redefinita metoda de afisare a numelui partenerului, cu posibilitatea de trimitere in context a parametrilor:
	- show_address_only - pentru afisare doar a adresei
	- show_address - afiseaza si adresa
	- show_email - afiseaza e-mail-ul
	- show_phone - afiseaza telefonul
	- show_category - afiseaza etichetele
- cautare directa partener dupa VAT



deltatech_credit_limit
======================
- posibilitate de verificare a limitei de credit la confirmarea comenzii de vanzare



deltatech_crm
=============
- preluare functionalitati de activitati din Odoo 9, inclusiv report-urile
- la creearea unui lead din mail, se preiau campurile din tag-urile speciale
- buton in oportunitate pentru afisarea comenzii de vanzare/ofreta asociate
- asignare template de mail la etapa unei oportunitati
- wizard pentru modoficarea in masa a agentului de vanzari la oportunitati



deltatech_crm_claim_8D
======================
- implementeaza sistemul de gestionare a problemelor "8D"
- poate functiona cu modulul CRM standard sau, daca nu este nevoie, se poate instala modulul deltatech_simple_crm (se face modificarea in __openerp__.py)



deltatech_crm_doc
=================
- gestionare documente legate de oportunitati



deltatech_crm_survey
====================
- adugarea de chestionar la un stadiu a oportunitatii/lead
- adugarea de chestionar la eticheta oportunitatii/lead
- adugare rezultate chestionar la oportunitate



deltatech_datecs_print
======================
- generare bon fiscal din factura pentru casa de marcat DATECS



deltatech_document
==================
- nr document automat dat de sistem, din categoria documentului
- campuri noi:
	- Description
	- Turtle reference
	- tipuri document Procedure, Template, Work Instruction
	- Departament
	- Reasons
	- Issued by: automat numele celui care creaza doc, numai administratorul poate avea acces de editare (asta daca vrea sa emite un doc in numele altei persoane)
	- Inform: in acest camp sa se poata selecta mai multi utilizatori care vor fi informati de noul document, revizie sau alte modificari.
	- Approved by : sa se poat selecta cel putin 1 utilizator care trebuie sa aprobe
- Documentul se inregistreaza in arhiva numai dupa ce a fost aprobat
- Documentele in stand by le pot vedea doar emitentii si cei care trebuie sa-l aprobe



deltatech_expenses
==================
- gestionarea decontului de cheltuieli
- Introducerea decontului de cheltuieli intr-un document distict ce genereaza automat chitante de achizitie 
- Validarea documentului duce la generarea notelor contabile de avans si inegistrarea platilor
- permite tiparirea decontului



deltatech_fast_sale
===================
- buton in comanda de vanzare pentru a face pasii de confirmare, livrare si facturare



deltatech_gamification
======================
- permite stabilirea unei tinte cu valoare negativa



deltatech_hr_attendance
=======================
- adaugare camp de data pentru raportarea prezentei



deltatech_invoice
=================
- calcul pret produs in functie de lista de preturi aferenta clientului/furnizorului
- validare data factura sa fie mai mare decat data din ultima factura
- nr. factura editabil
- permite 2 formulare pentru tiparirea facturii
- va fi revizuit


deltatech_invoice_number
========================
- wizard pentru modificarea numarului de factura



deltatech_invoice_product_filter
================================
- permite cautarea facturii dupa produs



deltatech_invoice_receipt
=========================
 - Adaugare buton nou in factura de receptie care  genereaza document de receptie stocuri  
 - Nu se permite achizitia unui produs stocabil fara comanda aprovizionare (picking in asteptare).
 - La creare factura din picking se face ajustarea automata a monedei de facturare in conformitate cu moneda din jurnal 
 - Adaugat buton pentru a genera un picking in asteptare in conformitate cu liniile din factura
 - Se permite generarea unei document de receptie pentru produsele care nu au comanda de achizitie
 - Pretul produselor se actualizeaza automat pentru receptiile fara comanda de achizitie
 - Furnizorul produselor se actualizeaza automat pentru receptiile fara comanda de achizitie 
 - Calcul pret produs in functie de lista de preturi aferenta clientului/furnizorului
 - buton in factura pentru afisarea stocului pentru produsele din factura
Antentie:
 - la inregistrarea facturilor in care sunt un produs apare de mai multe ori cu preturi diferite! Ia doar unul!
 
 
 
deltatech_invoice_report
========================
- Adaugare in raportul de analiza facturi a campurilor: judet, nr de factura si furnizor



deltatech_invoice_residual
==========================
- Calcul Sold factura in cazul in care totalul de pe facura este negativ, standard facturile nu au sold negativ



deltatech_invoice_weight
========================
- permite afisarea maselor (net, brut, pachet) in factura