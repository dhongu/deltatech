§### Plan pentru abordare hibridă: Integrarea `deltatech_website_sale_status` cu `deltatech_sale_stage`

Obiectivul este ca modulul de eCommerce (`website_sale_status`) să devină un "furnizor de automatizări" pentru sistemul de faze configurabile (`sale_stage`). Astfel, clientul poate defini fazele cum dorește, dar ele se vor schimba singure în funcție de fluxul de website/stoc/achiziții.

#### 1. Consolidarea Dependențelor
*   **`deltatech_sale_stage`**: Adăugarea `"deltatech_delivery_status"` în `depends` (pentru a corecta utilizarea `delivery_state`).
*   **`deltatech_website_sale_status`**: Adăugarea `"deltatech_sale_stage"` în `depends`. Aceasta va forța instalarea sistemului de faze atunci când se dorește statusul de website.

#### 2. Definirea Fazelor Standard (Data File)
Pentru ca automatizarea să funcționeze, avem nevoie de faze cu **coduri (codes)** specifice în `sale.order.phase`. Vom crea un fișier de date (`data/sale_order_phase_data.xml`) în `deltatech_website_sale_status` care să asigure existența acestor faze (dacă nu au fost deja create manual):
*   Coduri propuse: `placed`, `in_process`, `waiting`, `to_be_delivery`, `shipped`, `delivered`.

#### 3. Refactorizarea Modelului `sale.order` în `website_sale_status`
Vom modifica logica din `models/sale.py`:
*   **Eliminarea câmpului `stage`**: În loc de `stage = fields.Selection(...)`, vom folosi direct `phase_id` moștenit din `deltatech_sale_stage`.
*   **Redefinirea calculului automat**: Metoda `_compute_stage` (care ar putea fi redenumită `_compute_automatic_phase`) va apela metoda `set_phase(code)` din modulul `sale_stage`.
    *   *Exemplu logică:* `if order.state == 'sent' and order.website_id: order.set_phase('placed')`.
*   **Sincronizarea cu `stock.picking`**: Metoda `write` din `stock_picking.py` (în `website_sale_status`) va fi simplificată, apelând tot `sale_id.set_phase(...)`.

#### 4. Actualizarea Interfeței (Views)
*   În vederile de listă (`tree`) și formular (`form`) ale comenzii de vânzare din `website_sale_status`, vom înlocui câmpul `stage` cu `phase_id` sau `phase_ids` (cu widget-ul de badge-uri colorate deja existent în `sale_stage`).
*   Vom păstra filtrele de căutare, dar le vom mapa pe `phase_id.code`.

#### 5. Strategia de Migrare (pentru clienți existenți)
*   Pentru a nu pierde datele din câmpul `stage` actual, vom crea un script de migrare (post-init hook) care să citească valoarea din `stage` și să seteze `phase_id` corespunzător, după care câmpul `stage` poate fi eliminat definitiv.

#### Beneficii finale:
1.  **Flexibilitate maximă**: Utilizatorul poate decide dacă o fază automată (ex: `delivered`) trimite și un email sau execută o altă acțiune server, folosind interfața de configurare a fazelor.
2.  **Sursă unică de adevăr**: Nu mai avem două câmpuri de status care se bat cap în cap.
3.  **Extensibilitate**: Alte module pot adăuga noi automatizări apelând aceeași metodă `set_phase`.

**Dacă acest plan este în regulă, pot începe implementarea primului pas (corectarea manifestelor și pregătirea structurii de date).**
