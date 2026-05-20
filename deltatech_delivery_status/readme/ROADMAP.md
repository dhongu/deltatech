# ROADMAP — `deltatech_delivery_status`

**Versiune curentă:** 19.0.2.1.3
**Ultima actualizare:** 2026-05-20

Modul de **status livrare** — sincronizare status picking cu statusul plății și echipa de vânzări.
Depinde de: `delivery`, `stock`, `sales_team`, `stock_delivery`, `payment`.

---

## ✅ Realizat

- Sincronizare status `stock.picking` cu tranzacții de plată (`payment.transaction`)
- Integrare cu echipa de vânzări (`sales_team`) pentru vizibilitate livrări
- Câmpuri status livrare pe `sale.order`
- Teste de bază prezente (`tests/test_sale.py`)
- Migrare SQL pentru versiunea 14.0.2.0.1

---

## 🔴 Prioritate înaltă

### v19.0.2.2.0 — Stabilitate și calitate

- [ ] **1.1** Extinde testele existente din `test_sale.py`
  - Acoperă scenarii cu plată eșuată → status picking
  - Acoperă anulare comandă → revenire status
  - Adaugă teste pentru `payment_transaction.py` și `payment_provider.py`

- [ ] **1.2** Verifică compatibilitatea cu Odoo 19 Payment API
  - `payment.transaction` și `payment.provider` au schimbat API-ul în v17+
  - Testează fluxul complet plată → confirmare → livrare

- [ ] **1.3** Migrare SQL existentă doar pentru 14.0 — adaugă migrare pentru 19.0
  - Verifică dacă sunt câmpuri noi care necesită migrare de la versiunile anterioare

---

## 🟡 Prioritate medie

### v19.0.3.0.0 — Calitate cod

- [ ] **2.1** `stock_picking.py` (99 linii) — verifică că toate metodele override sunt compatibile cu Odoo 19
- [ ] **2.2** `sale_team.py` — documentează scopul câmpurilor adăugate pe echipa de vânzări
- [ ] **2.3** Adaugă `readme/DESCRIPTION.md` cu documentație utilizator
- [ ] **2.4** Verifică că nu există `.sudo()` fără comentariu justificativ

---

## 🟢 Prioritate scăzută

### v19.0.4.0.0 — Mentenanță

- [ ] **3.1** Mesaje de log în română — rescrie în engleză
- [ ] **3.2** Adaugă teste pentru `payment_provider.py` (14 linii — posibil neacoperit)
- [ ] **3.3** Revizuiește dependența de `stock_delivery` — verifică dacă este necesară sau poate fi înlocuită cu `delivery`

---

## 📌 Convenții versiuni

| Segment | Semnificație |
|---------|-------------|
| 19.0 | Odoo version |
| X | Major feature |
| Y | Minor feature / improvement |
| Z | Patch / bugfix |
