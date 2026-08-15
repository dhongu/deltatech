## 19.0.1.1.0 (2026-08-15)

**Fix** — jurnalul de activitate nu mai stochează conținutul câmpurilor binare.

Modificarea unui câmp binar al comenzii (eticheta AWB, semnătura) scria în
`activity_log` întregul conținut base64 al fișierului. Aceeași problemă a
umflat cu 1,7 GB baza unui client prin modulul echivalent pentru transferuri;
aici măsura este preventivă — la scara actuală jurnalul comenzilor rămâne mic,
dar `sale.order` are aceleași câmpuri binare.

Acum:

- câmpurile binare sunt ignorate complet la jurnalizare — nici nu mai sunt
  citite din filestore, deci scrierea pe comandă este și mai rapidă;
- valorile de câmp jurnalizate sunt scurtate la 200 de caractere (2000 pentru
  câmpurile x2many, descrise linie cu linie), cu marcarea numărului de
  caractere tăiate;
- mesajele din chatter sunt scurtate la 2000 de caractere;
- jurnalul unei zile este plafonat la 64 kB, păstrând activitatea recentă.
