# Roadmap: deltatech_sale_payment — Îmbunătățiri

## Rezolvate

### 1. ✅ Starea `pending` adăugată ca status distinct

Anterior, tranzacțiile `pending` apăreau ca `initiated`. Acum au propriul status distinct,
cu filtre și decorații dedicate.

### 2. ✅ `store=True` pe câmpurile computate

`payment_amount`, `payment_status` și `provider_id` sunt acum stocate în DB.
`@api.depends` complet: `amount_total`, `currency_id`, `transaction_ids.state/amount/provider_id`,
`invoice_ids.state/payment_state/amount_residual_signed/amount_total_signed/transaction_ids.is_post_processed`.
Datele existente populate prin migrare SQL `18.0.1.2.0/post_migrate.py`.

### 4. ✅ `provider_id` populat în migrare

Adăugat pasul 4 în `post_migrate.py`: populează `provider_id` pentru toate comenzile existente
cu prioritate `done > authorized > pending > cancel > orice`, folosind ultimul id din fiecare grup.
Legătura corectă `sale_order → account_move` se face prin
`sale_order_line → sale_order_line_invoice_rel → account_move_line → account_move`
(nu printr-un join direct, care producea produs cartezian).

### 3. ✅ Facturile `in_payment` excluse din `payment_amount`

Facturile cu `payment_state = 'in_payment'` (înregistrate dar nereconciliate cu banca) nu mai
sunt incluse în suma plătită — plata lor rămâne vizibilă prin tranzacțiile `done` direct.
Doar facturile `paid` și `partial` contribuie la `invoice_paid`.

### 4. ✅ `_search_payment_status` eliminat

Cu `store=True`, Odoo generează SQL direct pe coloană — nu mai e nevoie de metoda `_search`.
Eliminat împreună cu aproximările inexacte per status.

### 5. ✅ Decorații complete pentru `payment_status` în formular

| Status | Culoare |
|---|---|
| `done` | success (verde) |
| `partial`, `pending`, `initiated`, `authorized` | warning (galben) |
| `cancelled` | danger (roșu) |
| `without` | muted (gri) |

### 6. ✅ Filtre complete în lista de comenzi

Adăugate filtre pentru toate stările: fără plată, inițiată, în așteptare, autorizată,
efectuată, anulată.

### 7. ✅ `action_payment_link` — calcul sumă corect

Folosește `amount_residual` pe facturile postate în loc de `amount_total` pe toate facturile.

### 8. ✅ Teste actualizate și fixate

Fix `base_unit_count` în setUp (câmp required în Odoo 18 — folosit produs existent din DB).
Adăugate teste noi pentru `pending`, `cancelled`, `authorized`, combinații multiple.

---

## Rămase de rezolvat

### 9. Reconciliere automată după confirmare manuală

În `do_confirm()` din wizard, liniile de reconciliere sunt comentate:

```python
# transaction._finalize_post_processing()
# transaction._reconcile_after_transaction_done()
```

Fără ele, plata confirmată manual nu se leagă automat de factură.
De investigat compatibilitatea cu provider-ul `"none"` în Odoo 18.

### 10. Câmpul `payment_date` nu ajunge pe tranzacție

```python
# "date": self.payment_date,  ← comentat în wizard
```

Data plății selectată în wizard nu se stochează pe `payment.transaction`.

### 11. Teste lipsă pentru cazurile `partial`, `done` și wizard

- `test_compute_payment_partial_and_done` — comentat, necesită secvență `draft → pending → done`
- `test_sale_confirm_payment` — comentat
- `test_action_payment_link` — lipsă complet
