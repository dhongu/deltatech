# Ce e nou în 19.0 — Terrabit Connect (bază)

**Modul nou în 19.0.**

## Ce aduce
- **Puntea dintre Odoo din cloud și echipamentele din rețeaua locală a clientului** — casă de marcat, cântar, linie de sortare, PLC, server de etichete — pe care Odoo nu le poate accesa direct.
- **Registru de stații de lucru**, fiecare cu cheia ei de acces, cu ultima conectare și cu informațiile raportate (versiune de agent, sistem de operare, funcții active).
- **Apel HTTP în rețeaua clientului.** Stația interoghează periodic Odoo, iar canalul e refolosit în sens invers: Odoo poate cere stației să apeleze un echipament local și să întoarcă răspunsul.
- **Actualizare automată a agentului**, cu descărcarea versiunii noi prin Odoo (care păstrează acreditările), fără ca agentul instalat la client să dețină vreo cheie.
