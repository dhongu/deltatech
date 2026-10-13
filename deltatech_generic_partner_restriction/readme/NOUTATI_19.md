# Ce e nou în 19.0 — Restricții partener generic

## Stare în 19.0
Modulul a fost **comasat în „Partener generic"** (`deltatech_partner_generic`) și rămâne gol: păstrează
doar dependența, astfel încât bazele care îl au instalat să preia restricțiile la actualizare, fără
niciun pas manual. Funcționalitatea — jurnalele de plată restricționate și refuzul de a valida o factură
de client emisă pe partenerul generic — este neschimbată, doar că trăiește acum în celălalt modul, iar
jurnalele bifate sunt păstrate.

Instalările noi folosesc direct `deltatech_partner_generic`.
