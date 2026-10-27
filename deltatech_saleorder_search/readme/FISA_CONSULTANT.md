# Fișă Modul: Căutarea comenzilor după e-mailul sau telefonul clientului

**Modul:** `deltatech_saleorder_search`
**Utilizator principal:** Operator vânzări, operator relații cu clienții (call-center, suport magazin online)
**Prioritate:** 🟢 Scăzută (îmbunătățire de productivitate, fără impact asupra datelor)

---

## 1. Scop business

Clientul care sună sau scrie despre o comandă dă de obicei **adresa de e-mail sau numărul de telefon**,
nu numărul comenzii, iar la persoanele fizice numele poate fi scris în mai multe feluri. În Odoo
standard, căutarea comenzilor nu are criterii pe datele de contact ale clientului. Modulul adaugă în
bara de căutare a ofertelor și comenzilor două criterii noi, **E-mail** și **Phone**, care găsesc
comenzile după e-mailul sau telefonul clientului, inclusiv după o parte din ele.

## 2. Bază legală și context

Modul operațional, fără temei legal sau fiscal. Nu modifică date și nu generează documente. Căutarea
folosește doar datele de contact deja înregistrate pe client, în limita drepturilor utilizatorului
(un agent vede în rezultate doar comenzile pe care are dreptul să le vadă).

## 3. Utilizatori și roluri

| Rol | Utilizare |
|---|---|
| Operator vânzări / relații cu clienții | Găsește comenzile clientului după e-mail sau telefon |
| Manager vânzări | La fel, pe toate comenzile |

Nu există grupuri noi; criteriile sunt disponibile oricui are acces la Vânzări. Rol recomandat la
testare: **Vânzări: Utilizator: Toate documentele**.

## 4. Conturi și date implicate

Modulul nu atinge contabilitatea; nu există conturi implicate. Date folosite: **E-mail** și **Telefon**
de pe fișa clientului comenzii.

Date minime pentru demo: doi clienți cu e-mailuri și telefoane diferite (ex. `ana.pop@exemplu.ro`,
`+40 711 111 111` și `ion.ion@exemplu.ro`, `+40 722 222 222`) și câte o comandă pentru fiecare.

## 5. Configurare inițială

Nu necesită configurare. După instalare, criteriile apar automat în căutarea comenzilor. Verificați doar
că fișele clienților au e-mailul și telefonul completate.

## 6. Flux de utilizare

### Pasul 1 — Căutarea după e-mail

Deschideți **Vânzări → Comenzi → Oferte** sau **Vânzări → Comenzi → Comenzi**. Scrieți în bara de
căutare adresa de e-mail sau o parte din ea (ex. `ana.pop@`) și alegeți din lista derulantă **Căutare
E-mail pentru: …**. Lista păstrează comenzile al căror client are un e-mail care **conține** textul
scris; nu contează literele mari sau mici.

### Pasul 2 — Căutarea după telefon

Scrieți numărul sau o parte din el (ex. `711 111`) și alegeți **Căutare Phone pentru: …**. Textul se
caută exact cum este scris, ca fragment din numărul de telefon al clientului.

1. **Găsiți pe ecran** — în coloana **Client** apar doar comenzile clientului căutat.
2. **Verificați** — dacă lista e goală, comparați formatul scris cu cel de pe fișa clientului (spații,
   prefix `+40` sau `0`); un fragment mai scurt, fără spații și fără prefix, găsește mai multe variante.
3. **Treceți mai departe** — deschideți comanda dorită sau combinați criteriul cu filtrele standard
   (ex. **Comenzile mele**, perioadă).

### Note de monografie și raportare

Modulul **nu generează note contabile** și nu modifică date.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sale` | Căutarea ofertelor și comenzilor de vânzare, extinsă de modul |

**Ce e automat:** criteriile **E-mail** și **Phone** apar în toate listele de oferte și comenzi.

**Ce rămâne manual:** corectitudinea datelor de contact pe fișele clienților.

## 8. Verificări pentru consultant

- [ ] Căutarea **E-mail** după un fragment (`ana.pop@`) găsește doar comenzile clientului respectiv.
- [ ] Căutarea **E-mail** după domeniu (`@exemplu.ro`) găsește comenzile ambilor clienți.
- [ ] Căutarea **Phone** după `711 111` găsește comanda primului client.
- [ ] Căutarea **Phone** după un număr inexistent întoarce o listă goală.
- [ ] Criteriile apar atât în lista **Oferte**, cât și în lista **Comenzi**.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| Căutarea după telefon nu găsește comanda | Numărul e scris pe fișa clientului în alt format (spații, prefix) | Căutați după un fragment fără spații sau standardizați formatul pe fișe |
| Căutarea după e-mail nu găsește comanda | E-mailul e trecut pe o persoană de contact, nu pe clientul comenzii | Căutați după e-mailul clientului de pe comandă sau completați-l pe fișa lui |
| Comanda clientului nu apare, deși datele se potrivesc | Utilizatorul nu are drept să vadă comanda (ex. agent cu documente proprii) | Comportament corect al drepturilor |

## 10. Capturi de ecran

Fișa este **doar text**, fără capturi. Dacă se vor adăuga, capturile planificate, în ordinea pașilor:

| # | Fișier planificat | Conținut |
|---|---|---|
| 1 | `01_cautare_email.png` | Bara de căutare cu opțiunea **Căutare E-mail pentru** |
| 2 | `02_rezultat_telefon.png` | Lista de comenzi filtrată după **Phone** |

Generarea lor se face cu skill-ul `fisa-screenshots` (test `tests/test_screenshots.py`, mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`), în română.

## 11. Observații pentru manual

Treceți în manual, la capitolul despre găsirea comenzilor, cele două criterii noi și regula de bază:
**căutarea e după fragment**, deci un fragment scurt și fără spații dă cele mai bune rezultate la
telefon. Menționați că modulul caută după **E-mail** și **Telefon**; câmpul separat de mobil nu mai
există în Odoo 19, iar numerele de mobil se trec în **Telefon**. Eticheta **Phone** apare în engleză,
iar **E-mail** rămâne la fel în ambele limbi.
