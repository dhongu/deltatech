## 19.0.1.1.1 (2026-08-24)

**Fix** — jurnalizarea nu mai eșuează când o operație încă nesalvată este
ștearsă din formularul transferului.

Clientul web referă liniile nesalvate prin id-uri virtuale (`virtual_7149`).
Descrierea comenzilor pe câmpurile x2many citea acest id ca și cum ar fi unul
din baza de date, iar operația se termina cu `Expected singleton` — se pierdea
jurnalul întregii scrieri, inclusiv modificările legitime făcute în același
timp. Defectul a fost semnalat pe modulul echivalent pentru comenzi de vânzare,
care avea exact același cod.

Acum id-urile care nu sunt numerice sunt afișate ca text, iar o linie ștearsă
între timp este raportată prin id, fără a mai fi citită din baza de date.

## 19.0.1.1.0 (2026-08-15)

**Fix** — jurnalul de activitate nu mai stochează conținutul câmpurilor binare.

Modificarea unui câmp binar de pe transfer (eticheta AWB, semnătura) scria în
`activity_log` întregul conținut base64 al fișierului. Pe o instanță de
producție asta însemna o medie de 32 kB per înregistrare, cu vârfuri de 1,7 MB,
și circa 1,7 GB în baza de date la doar două luni de activitate păstrată.

Acum:

- câmpurile binare sunt ignorate complet la jurnalizare — nici nu mai sunt
  citite din filestore, deci scrierea pe transfer este și mai rapidă;
- valorile de câmp jurnalizate sunt scurtate la 200 de caractere (2000 pentru
  câmpurile x2many, descrise linie cu linie), cu marcarea numărului de
  caractere tăiate;
- mesajele din chatter sunt scurtate la 2000 de caractere;
- jurnalul unei zile este plafonat la 64 kB, păstrând activitatea recentă.
