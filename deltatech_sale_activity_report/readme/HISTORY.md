## 19.0.1.1.1 (2026-08-24)

**Fix** — jurnalizarea nu mai eșuează când o linie de comandă încă nesalvată
este ștearsă din formular.

Clientul web referă liniile nesalvate prin id-uri virtuale (`virtual_7149`).
Descrierea comenzilor pe `order_line` citea acest id ca și cum ar fi unul din
baza de date, iar operația se termina cu `Expected singleton` — se pierdea
jurnalul întregii scrieri, inclusiv modificările legitime făcute în același
timp, și rămânea un traceback în log la fiecare salvare de acest fel.

Acum id-urile care nu sunt numerice sunt afișate ca text, iar o linie ștearsă
între timp este raportată prin id, fără a mai fi citită din baza de date.

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
