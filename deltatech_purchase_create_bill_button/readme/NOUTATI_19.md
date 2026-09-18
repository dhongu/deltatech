# Ce e nou în 19.0 — Buton „Creează factură" la achiziții

**Modul nou în 19.0.**

## Ce aduce
- **Readuce butonul clasic „Creează factură" pe comanda de achiziție.** În Odoo 19 butonul a fost înlocuit cu un mecanism de încărcare care cere selectarea unui fișier înainte de a putea crea factura — o schimbare care încetinește operatorii care introduc facturile manual.
- **Copiază referința furnizorului** pe factura creată.

## 19.0.1.1.0
- **Readuce butonul „Creează facturi" și în lista comenzilor de achiziție** (lista „Cereri de ofertă", cea cu panoul de indicatori). În Odoo 19 butonul a rămas doar pe lista „Comenzi de achiziție", așa că selectarea mai multor comenzi din lista implicită nu mai permitea facturarea lor împreună. Se aplică și retururilor: dacă totalul e negativ, Odoo transformă automat documentul în factură storno furnizor.
