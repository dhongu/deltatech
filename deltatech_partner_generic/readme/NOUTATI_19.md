# Ce e nou în 19.0 — Partener generic

## Funcționalități noi
- **Restricțiile contabile sunt acum în același modul.** Ce nu se poate face cu partenerul generic —
  jurnalele de plată permise și refuzul de a valida o factură de client emisă pe el — era într-un modul
  separat, care trebuia instalat suplimentar. Acum vine odată cu partenerul generic, deci configurarea
  corectă nu mai depinde de a ști că există un al doilea modul.
- **Verificarea acoperă și adresa de livrare**, nu doar clientul de pe document.

## Îmbunătățiri
- **Partenerul generic este protejat împotriva modificărilor accidentale.** Fiind accesibil din orice
  document de vânzare, era ușor confundat cu un client obișnuit și redenumit, completat cu un CUI sau
  arhivat — cu efect asupra tuturor documentelor care îl folosesc.
- **Mesajul de refuz spune care câmp e de vină**, în locul unei erori generice pe care operatorul nu
  putea să o remedieze singur.

## La actualizare
Bazele care au instalat modulul separat de restricții preiau totul automat, fără intervenție manuală:
jurnalele bifate ca restricționate sunt păstrate de scriptul de migrare. Instalările noi au nevoie doar
de acest modul.
