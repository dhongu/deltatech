# Fișă Modul: Coduri alternative în magazinul online

**Modul:** `deltatech_alternative_website`
**Utilizator principal:** Administrator website, responsabil catalog de produse
**Prioritate:** 🟡 Medie (esențial pentru distribuitorii de piese, unde clienții caută după codul producătorului; fără impact contabil)

---

## 1. Scop business

La un distribuitor de piese de schimb sau de produse industriale, clientul nu caută după codul
intern al magazinului, ci după codul pe care îl are în mână: codul OEM, codul producătorului, un
număr de echivalență („cross-reference”). Modulul face ca aceste coduri alternative, ținute pe
produs de modulul `deltatech_alternative`, să fie găsite de căutarea din magazinul online și să
apară pe pagina produsului. Clientul care scrie `DIN933` în caseta de căutare găsește șurubul, chiar
dacă în catalog are alt cod intern. Pe pagina produsului, clienții autentificați văd codul
alternativ, iar toți vizitatorii văd, dacă e completat, la ce vehicul sau echipament se potrivește
piesa.

## 2. Bază legală și context

Nu există o obligație legală. Contextul este cel comercial: un client care nu găsește piesa după
codul pe care îl știe pleacă la concurență. Codurile alternative sunt puse în pagină și ca date
structurate (`itemprop="alternateName"`), pe care motoarele de căutare le pot citi; codurile
ascunse nu sunt publicate.

## 3. Utilizatori și roluri

- **Responsabil catalog** (utilizator intern cu drept pe produse) — completează codurile alternative
  și câmpul **Used For** (Utilizat la) pe produs.
- **Administrator website** — activează sau oprește blocurile de pe pagina produsului.
- **Vizitatorul magazinului** — caută după cod alternativ; vede secțiunea **Used For**.
- **Clientul autentificat** (portal) — vede în plus codul alternativ pe pagina produsului.

Roluri recomandate pentru testare:
- Administrator cu **modul de dezvoltare** activ.
- O fereastră privată de browser (vizitator public) și un utilizator portal, ca să comparați ce vede
  fiecare.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile și nu creează documente. Nu adaugă câmpuri noi: folosește
câmpurile din `deltatech_alternative`.

Date minime pentru demo:
- un produs publicat pe website (de ex. „Șurub hexagonal M8×20”);
- pe produs, în tab-ul **Alternative**, două coduri: `DIN933` și `ISO4017`, plus un al treilea cod
  cu bifa **Hide** (Ascuns), de ex. `COD-INTERN-01`;
- câmpul **Used For** (Utilizat la) completat, de ex. „Ford Focus 2005-2011”;
- un utilizator portal, pentru verificarea codului alternativ afișat.

## 5. Configurare inițială

1. Instalați modulul `deltatech_alternative_website`. Se instalează automat și `website_sale` și
   `deltatech_alternative`.
2. Deschideți produsul din **Vânzări → Produse → Produse** (sau **Inventar → Produse → Produse**).
3. În tab-ul **Alternative**, adăugați codurile alternative, câte unul pe rând. Ordinea se schimbă
   prin tragere. Bifați **Hide** pe codurile care nu trebuie să apară pe site.
4. În formular, sub prețul de cost, completați **Used For** (Utilizat la), dacă e cazul. Câmpul
   **Alternative Code** (Cod alternativ) de alături arată, separate prin „; ”, codurile neascunse.
5. Verificați că produsul este publicat pe website.

## 6. Flux de utilizare

### Pasul 1 — Clientul caută produsul după codul alternativ

Pe site, în magazin (`/shop`) sau în caseta de căutare din antet, clientul scrie codul alternativ,
de ex. `DIN933`. Căutarea magazinului include acum și codurile alternative ale produselor, alături
de denumire și codul intern, atât în lista de rezultate, cât și în sugestiile care apar în timp ce
scrie.

Înainte de căutare, textul introdus este curățat: spațiile de la început și de la sfârșit dispar,
iar mai multe spații consecutive devin unul singur. Astfel, `  DIN933 ` găsește același produs ca
`DIN933`.

**Ce verificați pe ecran:**
- produsul apare în rezultate când căutați oricare dintre codurile lui alternative, inclusiv cele
  marcate **Hide**: bifa ascunde codul doar pe pagina produsului, nu și din căutare;
- un cod parțial (de ex. `933`) găsește și el produsul, pentru că potrivirea este „conține”;
- căutarea nu caută în descrierea produsului, chiar dacă bara de căutare are activată afișarea
  descrierii; caută în denumire, coduri interne și coduri alternative.

### Pasul 2 — Pagina produsului pentru vizitatorul public

Clientul deschide produsul din rezultate. Pe pagina produsului, în formularul de cumpărare (zona cu
cantitatea și butonul de adăugare în coș), apare secțiunea
**Utilizat la:** (în engleză „User for:”, vezi secțiunea 9) cu valoarea câmpului **Used For**, de
ex. „Ford Focus 2005-2011”. Secțiunea lipsește dacă câmpul e gol.

Codurile alternative nu se văd pe ecran pentru vizitatorul public, dar sunt în pagină, ascunse, ca
date pentru motoarele de căutare. Codurile marcate **Hide** nu sunt incluse.

### Pasul 3 — Pagina produsului pentru clientul autentificat

Același produs, deschis de un client autentificat (utilizator portal sau intern), arată în plus,
după o linie de separare, eticheta **Cod Alternativ:** urmată de codurile neascunse, separate prin
„; ” (de ex. `DIN933; ISO4017`).

**Ce verificați pe ecran:**
- vizitatorul public nu vede eticheta **Cod Alternativ:**;
- clientul autentificat o vede, fără codul marcat **Hide**.

### Pasul 4 — Activarea sau oprirea blocurilor de pe pagina produsului

Cele două blocuri sunt vizualizări opționale ale paginii de produs, active după instalare:
**Alternative code** (codurile alternative) și **Used For** (secțiunea „Utilizat la”). În Odoo 19
ele nu au un comutator în panoul editorului de website, așa că se opresc din vizualizări: cu modul
de dezvoltare activ, **Setări → Tehnic → Interfață utilizator → Vizualizări**, căutați după nume
(„Alternative code” sau „Used For”), deschideți vizualizarea și debifați **Activ**. Când website-ul
are o copie proprie a vizualizării (după ce pagina produsului a fost editată), opriți copia
website-ului respectiv.

Oprirea blocului **Alternative code** scoate din pagină și codurile ascunse pentru motoarele de
căutare, dar nu și căutarea după cod alternativ în magazin, care rămâne activă.

### Note de monografie și raportare

Modulul nu generează note contabile și nu are rapoarte. Nu scrie nimic în baza de date: schimbă
doar căutarea magazinului și afișarea paginii de produs.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux | Tip legătură |
|---|---|---|
| `deltatech_alternative` | ține codurile alternative pe produs (tab-ul **Alternative**, bifa **Hide**) și câmpul **Used For**; caută după cod alternativ și în comenzi și documente interne | dependență (manifest) |
| `website_sale` | magazinul, pagina produsului și căutarea extinsă de modul | dependență (manifest) |
| `website` | caseta de căutare și sugestiile automate | dependență (manifest) |

Ce este automat: includerea codurilor alternative în căutarea magazinului și în sugestii,
curățarea spațiilor din textul căutat, afișarea codului și a secțiunii „Utilizat la” pe pagina
produsului.
Ce rămâne manual: introducerea codurilor alternative pe fiecare produs (sau importul lor), alegerea
codurilor ascunse și completarea câmpului **Used For**.

## 8. Verificări pentru consultant

- [ ] Căutarea în magazin după un cod alternativ găsește produsul.
- [ ] Sugestiile din caseta de căutare includ produsul când scrieți codul alternativ.
- [ ] Un cod marcat **Hide** nu apare pe pagina produsului, nici ascuns pentru motoarele de căutare,
  dar produsul se găsește în magazin și după el.
- [ ] Textul căutat cu spații în plus găsește aceleași produse ca fără ele.
- [ ] Vizitatorul public nu vede eticheta **Cod Alternativ:**; clientul autentificat o vede.
- [ ] Secțiunea **Utilizat la:** apare doar pe produsele cu **Used For** completat.
- [ ] Căutarea funcționează și când bara de căutare are afișarea descrierii pornită sau oprită.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|-----------------|-----------------|-----------|
| Produsul nu e găsit după codul alternativ | produsul nu e publicat pe website sale, ori codul e scris diferit (alt separator, cratimă) | publicați produsul; adăugați și varianta de scriere folosită de clienți ca alt cod alternativ |
| Clientul nu găsește un produs după un cuvânt din descriere | modulul scoate descrierea din câmpurile căutate, ca să nu aducă rezultate nepotrivite | comportament intenționat; puneți termenul în denumire sau ca un cod alternativ |
| Pe site-ul în engleză, eticheta apare „User for:” în loc de „Used for:” | greșeală de scriere în șablon; în română eticheta e corectă („Utilizat la:”) | semnalată ca bug ([#3823](https://github.com/dhongu/deltatech/issues/3823)); până la corectare, se poate traduce eticheta în engleză din editorul de traduceri |
| Codul alternativ nu apare pe pagina produsului | vizitatorul nu e autentificat, toate codurile sunt marcate **Hide**, ori vizualizarea **Alternative code** a fost oprită | autentificați-vă, verificați bifa **Hide** și starea vizualizării |
| Căutarea întoarce o eroare `list.remove(x)` | versiune veche a modulului, cu afișarea descrierii oprită pe bara de căutare | actualizați modulul (corectat în 19.0.1.0.8) |

## 10. Capturi de ecran

Fișa este, deocamdată, doar text: nu are capturi de ecran. Pașii din secțiunea 6 descriu ecranele
în cuvinte. Când se vor adăuga capturi, se generează cu skill-ul `fisa-screenshots` (mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`, în română), câte una pentru fiecare pas.

## 11. Observații pentru manual

Explicați clientului că valoarea modulului vine din date: codurile alternative trebuie introduse
(sau importate) pe produse, iar fiecare variantă de scriere folosită de clienți (cu sau fără spații,
cu cratimă) poate fi adăugată ca cod separat. Precizați diferența de afișare între vizitatorul
public și clientul autentificat, ca să nu fie raportată ca eroare. Bifa **Hide** ascunde codul
de pe pagina produsului, dar clientul care îl știe găsește totuși produsul în căutarea magazinului;
un cod care nu trebuie deloc expus nu se pune ca cod alternativ.
