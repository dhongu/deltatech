# Fișă Modul: Tipărirea etichetelor Zebra din rapoarte PRN

**Modul:** `deltatech_report_prn`
**Utilizator principal:** Consultant tehnic (definește raportul); operator de depozit sau recepție (tipărește etichetele)
**Prioritate:** 🟡 Medie (modul tehnic, dar de el depinde tipărirea etichetelor pe imprimantele Zebra)

---

## 1. Scop business

Imprimantele de etichete Zebra primesc comenzi în limbajul ZPL, nu PDF. Modulul adaugă în Odoo un
tip de raport nou, **PRN**: raportul se scrie ca un șablon QWeb care produce text ZPL, iar la
tipărire Odoo descarcă un fișier `.prn` în locul unui PDF. Pe stația de lucru, fișierul `.prn`
este trimis la imprimantă (de obicei printr-un script `.bat` asociat extensiei `.prn`).

Așa se pot tipări din Odoo etichete de produs, de lot sau de colet cu formatul exact al imprimantei,
fără conversie PDF și fără driver de imprimantă grafic.

## 2. Bază legală și context

Modulul nu are implicații contabile sau fiscale. Contextul este operațional: etichetarea
produselor, loturilor și coletelor în depozit, la recepție sau la expediere.

Trimiterea la imprimantă se face **de pe stația de lucru**, nu de pe server: pe Odoo.sh serverul nu
are acces la rețeaua locală a clientului. Tipărirea directă prin Zebra Browser Print (fără
descărcarea fișierului) este oferită de un modul companion separat, privat,
`deltatech_report_prn_zebra_sdk`; acest modul îi oferă doar punctul de extensie și rămâne varianta
de rezervă (descărcarea fișierului `.prn`).

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Consultant tehnic / dezvoltator | Creează raportul de tip **PRN** și șablonul ZPL; configurează stațiile de lucru |
| Operator (depozit, recepție, vânzări) | Tipărește eticheta din meniul **Tipăriți** al documentului |

Modulul nu adaugă grupuri de drepturi. Crearea rapoartelor cere modul dezvoltator și drepturi de
administrare; tipărirea cere doar dreptul de citire pe documentul de pe care se tipărește.

## 4. Conturi și date implicate

Nu se folosesc conturi contabile. Pentru demo sunt necesare:

- un raport (acțiune de raport) cu **Tip raport** = **PRN**, legat de un model (de exemplu produse sau
  transferuri) și cu un șablon QWeb care produce text ZPL;
- o înregistrare a modelului respectiv (un produs, un transfer);
- pe stația de lucru, asocierea extensiei `.prn` cu un script care trimite fișierul la imprimantă.

## 5. Configurare inițială

1. Instalați modulul `deltatech_report_prn` (depinde doar de `web`).
2. Activați modul dezvoltator și deschideți **Setări → Tehnic → Acțiuni → Rapoarte**
   (*Settings → Technical → Actions → Reports*).
3. Creați sau deschideți raportul de etichetă și setați **Tip raport** (*Report Type*) = **PRN**.
   Șablonul QWeb al raportului trebuie să producă text ZPL (comenzi `^XA ... ^XZ`), nu HTML.
4. Opțional, completați numele fișierului tipărit (expresia *Printed Report Name*), de exemplu cu
   codul produsului; altfel fișierul se numește după raport.
5. În meniul **Tipăriți** al modelului, raportul apare dacă are legătura de meniu (*Add in the Print
   menu*).
6. Pe fiecare stație de lucru: asociați extensia `.prn` cu un script `.bat` care copiază fișierul la
   imprimantă (de exemplu prin `copy /b` către imprimanta partajată) și setați browserul să deschidă
   automat fișierele `.prn` descărcate.

## 6. Flux de utilizare

### Pasul 1 — Tipărirea etichetei

Operatorul deschide documentul (produsul, transferul) sau selectează mai multe înregistrări în listă,
apoi alege raportul din meniul **Tipăriți** (*Print*). Ecranul se blochează scurt cât Odoo pregătește
fișierul.

### Pasul 2 — Descărcarea fișierului `.prn`

Browserul descarcă un fișier `.prn`:

- pentru o singură înregistrare, cu numele dat de expresia *Printed Report Name*, dacă există;
- pentru mai multe înregistrări, sau fără expresie, cu numele raportului.

Fișierul conține textul ZPL al tuturor etichetelor selectate.

### Pasul 3 — Trimiterea la imprimantă

Pe stația configurată, fișierul `.prn` se deschide automat cu scriptul asociat, care îl trimite la
imprimanta Zebra. Operatorul verifică eticheta tipărită: format, cod de bare lizibil, date corecte.

Dacă modulul companion pentru Zebra Browser Print este instalat și activ, eticheta se trimite direct
la imprimantă, fără descărcare; dacă serviciul Browser Print nu răspunde, Odoo revine la descărcarea
fișierului `.prn` de la pasul 2.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr).

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `web` | Dependență: acțiunile de raport și descărcarea fișierelor |
| `deltatech_report_prn_zebra_sdk` (privat, opțional) | Tipărire directă prin Zebra Browser Print, cu revenire la descărcarea `.prn` |
| Module sau personalizări cu șabloane ZPL | Definesc rapoartele de etichetă de tip **PRN** |

**Ce e automat:** randarea șablonului ca text, numele fișierului, descărcarea fișierului `.prn`.

**Ce rămâne manual:** scrierea șablonului ZPL, configurarea fiecărei stații de lucru (asocierea
extensiei și scriptul), verificarea etichetei tipărite.

## 8. Verificări pentru consultant

- [ ] Câmpul **Tip raport** al unei acțiuni de raport oferă valoarea **PRN**.
- [ ] Raportul **PRN** apare în meniul **Tipăriți** al modelului legat.
- [ ] La tipărire se descarcă un fișier cu extensia `.prn`, nu un PDF.
- [ ] Pentru o singură înregistrare, numele fișierului urmează expresia *Printed Report Name*.
- [ ] Conținutul fișierului este text ZPL (începe cu `^XA`), fără HTML.
- [ ] Pe stația configurată, fișierul ajunge la imprimantă și eticheta este corectă.
- [ ] La selecția mai multor înregistrări, fișierul conține câte o etichetă pentru fiecare.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| Se descarcă fișierul, dar nu se tipărește nimic | Extensia `.prn` nu este asociată cu scriptul pe stația de lucru, sau browserul nu deschide automat fișierul | Configurați asocierea extensiei și deschiderea automată în browser |
| Imprimanta tipărește text sau etichete goale | Șablonul produce HTML sau ZPL invalid | Corectați șablonul raportului (doar comenzi ZPL) |
| Raportul nu apare în meniul **Tipăriți** | Raportul nu are legătura de meniu | Activați *Add in the Print menu* pe raport |
| La dezinstalarea modulului, raportul devine PDF | Tipul **PRN** dispare, iar rapoartele lui revin la tipul implicit | Reinstalați modulul sau schimbați manual tipul rapoartelor |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are capturi ale fluxului în `static/description/` (acolo sunt doar
iconița și imaginea principală pentru Odoo Apps) și nici test `tests/test_screenshots.py`. Fluxul
este în mare parte în afara Odoo (fișierul descărcat și imprimanta), iar modulul nu are un raport
**PRN** propriu de captat; capturile (tipul de raport **PRN** în formularul raportului, meniul
**Tipărire**) se pot genera ulterior cu skill-ul `fisa-screenshots`, dintr-un modul care definește un
astfel de raport.

## 11. Observații pentru manual

- Manualul operatorului descrie doar pașii 1–3; configurarea raportului și a stațiilor de lucru este
  sarcina consultantului.
- Fiecare stație de lucru nouă (sau profil Windows nou) trebuie configurată din nou pentru `.prn`.
- Pe termen lung, tipărirea prin Zebra Browser Print (modulul companion) înlocuiește scriptul `.bat`;
  vezi `readme/ROADMAP.md`.
