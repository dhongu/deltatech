# Fișă Modul: Protecția istoricului din chatter-ul produselor

**Modul:** `deltatech_product_chatter`
**Utilizator principal:** Administrator Odoo / responsabil de nomenclator (decide cine poate șterge
mesaje), orice utilizator care scrie în chatter-ul produselor
**Prioritate:** 🟡 Medie (control intern asupra istoricului produselor, fără efect contabil)

---

## 1. Scop business

Chatter-ul produsului păstrează istoricul lui: notele interne ale echipei (o reclamație de la un
client, o discuție cu furnizorul, motivul unei schimbări de preț), mesajele trimise și urmărirea
modificărilor. În Odoo standard, autorul unui mesaj îl poate edita sau șterge oricând, iar istoricul
se poate pierde fără urmă. Modulul **blochează ștergerea și editarea mesajelor din chatter-ul
produselor** pentru toți utilizatorii, cu excepția celor dintr-un grup dedicat, **Sterge mesaje
Chatter produs**. Astfel, ce s-a scris pe un produs rămâne, iar corecturile le face doar o persoană
de încredere.

## 2. Bază legală și context

- Modulul **nu are efect fiscal sau contabil** și nu modifică datele produselor.
- Contextul este de **control intern**: istoricul unui produs (reclamații, decizii de preț, discuții
  cu furnizorii) este o urmă de audit. Restricția ajută la păstrarea ei, dar nu înlocuiește
  arhivarea documentelor justificative cerută de legislația contabilă.
- Restricția se aplică doar mesajelor de pe **produse** și **variante de produs**. Chatter-ul
  celorlalte documente (comenzi, facturi, contacte) funcționează ca în Odoo standard.

## 3. Utilizatori și roluri

| Rol | Ce poate face |
|---|---|
| Utilizator fără grupul **Sterge mesaje Chatter produs** | scrie mesaje și note pe produse, dar nu le poate edita și nu le poate șterge, nici pe ale lui |
| Utilizator cu grupul **Sterge mesaje Chatter produs** | editează și șterge mesajele de pe produse, după regulile Odoo standard (de regulă, mesajele proprii; administratorul, pe toate) |
| **Administrare: Setări** | acordă sau retrage grupul utilizatorilor |

La instalare, grupul este acordat utilizatorului **Administrator** (și utilizatorului intern de
sistem).

Roluri recomandate pentru testare:
- un **agent de vânzări** fără grup, care încearcă să-și șteargă propria notă de pe un produs;
- un **responsabil de nomenclator** căruia i se acordă grupul, care șterge aceeași notă.

## 4. Conturi și date implicate

Modulul **nu generează note contabile** și nu atinge conturi. Date minime pentru demo:

- produsul **Cană ceramică 350 ml**, cu o notă internă scrisă de agentul de vânzări: „Client Casa
  Verde SRL a reclamat ciobituri la lotul din septembrie”;
- utilizatorul **Agent Vânzări** (fără grup) și utilizatorul **Responsabil Nomenclator** (cu grup).

## 5. Configurare inițială

1. Instalați `deltatech_product_chatter` (dependențe: `product`, `mail`). Imediat după instalare,
   toți utilizatorii în afară de Administrator pierd dreptul de a edita sau șterge mesajele de pe
   produse.
2. Stabiliți cine are voie să corecteze istoricul produselor și acordați-i grupul (secțiunea 6,
   pasul 1). Recomandat: cât mai puține persoane.

## 6. Flux de utilizare

### Pasul 1 — Acordarea grupului unui utilizator de încredere

Deschideți **Setări → Utilizatori & Companii → Utilizatori**, alegeți utilizatorul (de exemplu
„Responsabil Nomenclator”) și mergeți în fila **Drepturi de acces**. În categoria **Date de bază**,
la rubrica **Produse**, selectați **Sterge mesaje Chatter produs**. Salvați.

Pentru a retrage dreptul, deselectați grupul în același loc.

### Pasul 2 — Utilizator fără grup: ștergerea este refuzată

Autentificat ca „Agent Vânzări”, deschideți produsul din **Vânzări → Produse → Produse** sau
**Inventar → Produse → Produse**. În chatter, treceți cu mouse-ul peste nota scrisă de el și alegeți
din acțiunile mesajului **Șterge** (sau **Editare**, pentru a-i schimba textul).

Odoo refuză operația cu mesajul: „Nu aveți permisiunea de a șterge sau edita mesajele din chatter pe
produse. Cereți unui administrator să vă acorde grupul 'Șterge mesaje Chatter produs'.” Nota rămâne
neschimbată în chatter.

**Verificați:** după ce închideți mesajul de eroare și reîncărcați pagina, nota este tot acolo, cu
textul inițial.

### Pasul 3 — Utilizator cu grup: ștergerea funcționează

Autentificat ca „Responsabil Nomenclator” (pasul 1), deschideți același produs și ștergeți sau
editați un mesaj propriu. Operația se face ca în Odoo standard. Pentru mesajele altor utilizatori se
aplică în continuare regulile Odoo: de regulă, doar autorul sau administratorul le poate modifica.

### Pasul 4 — Restul aplicației nu este afectat

Autentificat din nou ca „Agent Vânzări”, deschideți o comandă de vânzare și ștergeți o notă proprie
din chatter-ul ei: operația funcționează. Restricția privește doar produsele și variantele de produs.

Ștergerea unui **produs** întreg (de către cine are dreptul) șterge și mesajele lui, ca în Odoo
standard; modulul nu o blochează.

### Note de monografie și raportare

Modulul **nu înregistrează nicio notă contabilă** și nu adaugă rapoarte. Blocarea se aplică și
ștergerilor făcute din afara ecranului (importuri, scripturi, integrări prin API) rulate cu un
utilizator fără grup.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux |
|---|---|
| `product` | produsele și variantele de produs, al căror chatter este protejat; categoria de drepturi **Produse** |
| `mail` | chatter-ul și acțiunile **Editare** / **Șterge** ale mesajelor |

Ce este automat: blocarea editării și ștergerii pentru utilizatorii fără grup, acordarea grupului
către Administrator la instalare.

Ce rămâne manual: alegerea și acordarea grupului utilizatorilor de încredere.

## 8. Verificări pentru consultant

- [ ] În fila **Drepturi de acces** a utilizatorului, categoria **Date de bază**, rubrica **Produse**
      are opțiunea **Sterge mesaje Chatter produs**.
- [ ] Un utilizator fără grup nu poate șterge propria notă de pe un produs; primește mesajul de
      permisiune, iar nota rămâne.
- [ ] Un utilizator fără grup nu poate edita textul propriei note de pe un produs.
- [ ] Același lucru este valabil pe o variantă de produs (**Inventar → Produse → Variante produs**,
      dacă variantele sunt activate).
- [ ] Un utilizator cu grup șterge și editează mesajele proprii de pe produs.
- [ ] Chatter-ul comenzilor, facturilor și contactelor funcționează ca înainte pentru utilizatorul
      fără grup.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| „Nu aveți permisiunea de a șterge sau edita mesajele din chatter pe produse. …” | Utilizatorul nu are grupul **Sterge mesaje Chatter produs** | Dacă este o persoană de încredere, acordați-i grupul (pasul 1); altfel, mesajul rămâne |
| Un import sau o integrare care curăță mesaje pe produse se oprește cu eroare de acces | Rulează cu un utilizator fără grup | Rulați-o cu un utilizator care are grupul sau renunțați la ștergerea mesajelor de produs |
| Utilizatorul cu grup tot nu poate șterge un mesaj | Mesajul este al altui utilizator; Odoo permite modificarea doar autorului sau administratorului | Cereți autorului sau administratorului să-l modifice |

## 10. Capturi de ecran

Fișa este, deocamdată, **doar text**: nu are capturi de ecran. Capturile planificate, în ordinea
pașilor din secțiunea 6:

1. `01_utilizator_grup_chatter.png` — fila „Drepturi de acces” a utilizatorului, cu grupul „Sterge mesaje Chatter produs”.
2. `02_stergere_refuzata.png` — mesajul de permisiune la ștergerea unei note de pe produs.
3. `03_stergere_permisa.png` — chatter-ul produsului după ștergerea notei de către utilizatorul cu grup.
4. `04_comanda_neafectata.png` — chatter-ul unei comenzi de vânzare, unde ștergerea funcționează.

Ele se pot genera ulterior cu skill-ul `fisa-screenshots` (test `tests/test_screenshots.py`, mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`), în limba română, după care se leagă în pașii din
secțiunea 6.

## 11. Observații pentru manual

Prezentați modulul ca o **protecție a istoricului produselor**: oricine scrie, dar doar câțiva pot
corecta. Avertizați clientul că, imediat după instalare, nici autorii nu își mai pot corecta notele
de pe produse, așa că grupul trebuie acordat de la început persoanei care face corecturile. Numele
grupului apare în română fără diacritice („Sterge”), iar în mesajul de eroare cu diacritice
(„Șterge”): este același grup.
