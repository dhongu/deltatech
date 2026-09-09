# ROADMAP — `deltatech_delivery_status`

**Versiune curentă:** 19.0.2.3.0
**Ultima actualizare:** 2026-09-09

Modul de **status livrare** — urmărirea granulară a stării coletului, amânarea
livrării în funcție de plată și integrarea cu echipa de vânzări.
Depinde de: `delivery`, `stock`, `sales_team`, `stock_delivery`, `payment`.

---

## ✅ Realizat

- Sincronizare status `stock.picking` cu tranzacții de plată (`payment.transaction`)
- Amânare/eliberare livrare la nivel de comandă, cu acțiuni server pentru operare în masă
- `postponed_delivery` căutabil (metodă `search` peste `picking_ids.postponed`),
  plus filtre în căutarea comenzilor și a transferurilor (19.0.2.3.0)
- Fix: eliberarea livrării la confirmarea plății folosea câmpul inexistent
  `payment.transaction.sale_order_id` (19.0.2.1.4)
- Fix: validarea unui transfer fără curier nu mai marchează livrarea ca
  `delivered`; marcarea trece în cronul din `deltatech_delivery` (19.0.2.2.0)
- Compatibilitate cu Payment API din Odoo 19 verificată pe fluxul
  plată → confirmare → eliberare livrare
- Integrare cu echipa de vânzări (`sales_team`) pentru amânarea plăților prin transfer bancar
- `readme/DESCRIPTION.md` complet (stări de livrare, blocare livrare, disponibilitate)
- 5 teste în `tests/test_sale.py` — recalcul `postponed_delivery`, validare fără
  curier, eliberare la plată confirmată, căutare pe `postponed_delivery`
- Mesajele de log sunt în engleză

---

## 🔴 Prioritate înaltă

### v19.0.2.4.0 — Acoperire de test pe scenariile negative

- [ ] **1.1** Test pentru plată eșuată / anulată — comanda amânată trebuie să
      rămână amânată, iar `_set_done` să nu o elibereze
- [ ] **1.2** Test pentru anularea comenzii — ce se întâmplă cu transferurile
      amânate rămase în urmă
- [ ] **1.3** Test pentru `_create_backorder` cu parametrul `backorders.postponed`
      activ — restanța moștenește `postponed`

---

## 🟡 Prioritate medie

### v19.0.3.0.0 — Calitate cod

- [ ] **2.1** Migrarea SQL existentă acoperă doar 14.0.2.0.1 — verifică dacă
      trecerea de la versiunile 17/18 la 19 cere pași de migrare pentru
      `delivery_state` / `postponed`
- [ ] **2.2** `crm.team.postpone_payment_transfer` nu are `help` — documentează
      că se aplică doar plăților cu `custom_mode == "wire_transfer"`
- [ ] **2.3** Cele patru apeluri `.sudo()` (`models/sale.py`,
      `models/stock_picking.py`) au nevoie de comentariu justificativ
- [ ] **2.4** `_action_confirm` citește ultima tranzacție cu `_get_last()` și
      cade pe `transaction_ids[-1]` — verifică dacă fallback-ul mai e necesar în 19

---

## 🟢 Prioritate scăzută

### v19.0.4.0.0 — Mentenanță

- [ ] **3.1** Revizuiește dependența de `stock_delivery` — verifică dacă mai e
      necesară sau poate fi acoperită de `delivery`
- [ ] **3.2** Parametrul de sistem `backorders.postponed` nu e expus în interfață
      și nu apare în `readme/CONFIGURE.md`

---

## 📌 Convenții versiuni

| Segment | Semnificație |
|---------|-------------|
| 19.0 | Odoo version |
| X | Major feature |
| Y | Minor feature / improvement |
| Z | Patch / bugfix |
