# Fișă Modul: Linii suplimentare automate în Punctul de vânzare

**Modul:** `deltatech_sale_add_extra_line_pos`
**Utilizator principal:** Casier (POS); consultantul configurează produsele
**Prioritate:** 🟡 Medie (evită omiterea taxelor și a produselor însoțitoare la casă)

---

## 1. Scop business

Unele produse se vând obligatoriu împreună cu un alt articol: o garanție (SGR) pe sticlă, o taxă de
mediu, o pungă, un ambalaj, o taxă de serviciu. Casierul uită ușor să le adauge. Modulul duce în
**Punctul de vânzare (POS)** regula din `deltatech_sale_add_extra_line`: când casierul adaugă în coș
un produs care are configurat un **Produs suplimentar**, POS-ul adaugă automat și linia produsului
suplimentar, cu cantitatea calculată, și o ține sincronizată cu produsele principale din bon.

## 2. Bază legală și context

Modulul nu are temei legal propriu. Este folosit des pentru sume pe care legea le cere evidențiate
separat pe bon (de exemplu garanția sistemului de returnare a ambalajelor SGR sau taxe de mediu);
obligația de afișare separată vine din reglementarea respectivei taxe, nu din modul. Tratamentul
fiscal (TVA, cont) este cel al produsului suplimentar, configurat ca orice produs.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Consultant / administrator vânzări | Configurează pe produs **Produsul suplimentar** și **Cantitatea suplimentară** |
| Casier (Punct de vânzare / Utilizator) | Vinde produsele; linia suplimentară apare și se actualizează singură |

Modulul nu adaugă grupuri sau drepturi proprii. Roluri recomandate pentru testare: un administrator
POS (configurare) și un casier (vânzare).

## 4. Conturi și date implicate

Modulul nu folosește conturi proprii: linia suplimentară este o linie obișnuită de bon, contabilizată
la închiderea sesiunii după contul de venit și taxele produsului suplimentar. Date minime pentru demo:

- un produs suplimentar (ex. „Garanție SGR”, preț 0,50 lei), **Disponibil în POS**;
- 1–2 produse principale (ex. „Apă 0,5 l”), **Disponibile în POS**, care au acest produs
  suplimentar configurat;
- un punct de vânzare cu o sesiune deschisă.

## 5. Configurare inițială

1. Instalați modulul `deltatech_sale_add_extra_line_pos` (instalează și `deltatech_sale_add_extra_line`
   și `point_of_sale`).
2. Deschideți produsul suplimentar din **Punct de vânzare → Produse → Produse** și bifați
   disponibilitatea în POS. **Fără această bifă, linia suplimentară nu se adaugă în POS.**
3. Deschideți produsul principal, pagina **Vânzări**, grupul **Linie suplimentară** (*Extra Line*):
   - **Produs suplimentar** (*Extra Product*) — produsul adăugat automat;
   - **Cantitate suplimentară** (*Extra Qty*) — multiplicatorul cantității (implicit 1; ex. 6 pentru un
     bax de 6 sticle cu garanție per sticlă).
   Câmpul **Procent suplimentar** (*Extra Percent*) se folosește doar pe comenzile de vânzare; în POS
   linia suplimentară are prețul produsului suplimentar.
4. Dacă o sesiune POS era deja deschisă, reîncărcați POS-ul ca să preia configurarea produselor.

## 6. Flux de utilizare

### Pasul 1 — Adăugarea produsului principal

Casierul deschide sesiunea din **Punct de vânzare → Panou de control → Deschide registrul** și
adaugă în coș produsul principal (clic pe produs sau scanare cod de bare).

- Imediat după linia principală apare linia produsului suplimentar, cu cantitatea
  `cantitatea produsului principal × Cantitate suplimentară`.
- Pentru un produs cântărit, configurat cu variante sau cu lot, cantitatea se ia din linia acceptată
  (greutatea citită, cantitatea confirmată), nu din cantitatea cerută.
- Dacă casierul anulează fereastra de configurare, lot sau cântărire, nu se adaugă nici produsul
  principal, nici linia suplimentară.

### Pasul 2 — Modificarea cantității

Casierul schimbă cantitatea produsului principal (de la tastatura numerică sau adăugând din nou
același produs). Cantitatea liniei suplimentare se recalculează pe loc.

Dacă mai multe produse din bon au **același** produs suplimentar, acesta apare pe **o singură linie**,
cu cantitatea totală: `Σ (cantitate produs principal × Cantitate suplimentară)`.

### Pasul 3 — Ștergerea unei linii principale

Casierul șterge linia produsului principal. Cantitatea liniei suplimentare scade corespunzător; dacă
niciun produs din bon nu mai cere produsul suplimentar, linia lui se șterge și ea.

### Pasul 4 — Retur

La un retur, cantitatea produsului principal este negativă, iar linia suplimentară se creează tot cu
cantitate negativă, deci garanția sau taxa se restituie împreună cu produsul.

### Pasul 5 — Plata și bonul

Casierul încasează bonul ca de obicei. Pe bon, produsul suplimentar apare ca linie separată, cu
prețul și taxa lui. La închiderea sesiunii, liniile se contabilizează împreună cu restul vânzărilor.

### Note de monografie și raportare

Modulul nu generează note contabile proprii. La închiderea sesiunii POS, linia suplimentară intră în
nota de vânzare a sesiunii ca orice produs:

| Dr | Cr | Sumă |
|---|---|---|
| 5311 Casa în lei / 5125 Sume în curs de decontare (card) | 70x Venituri (contul produsului suplimentar) | valoarea fără TVA a liniei suplimentare |
| 5311 / 5125 | 4427 TVA colectată | TVA-ul liniei, după taxa produsului suplimentar |

Linia de TVA lipsește când produsul suplimentar nu are taxă, cum este cazul garanției SGR, care nu
intră în baza de impozitare a TVA. Conturile exacte sunt cele configurate pe produsul (categoria)
suplimentar și pe metodele de plată.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `deltatech_sale_add_extra_line` | câmpurile de configurare pe produs; aceeași regulă pe comenzile de vânzare și în magazinul online |
| `point_of_sale` | interfața de vânzare în care se adaugă liniile |
| `deltatech_pos` / `deltatech_ecr_connect` | tipărirea bonului fiscal; linia suplimentară apare pe bonul fiscal ca articol separat |
| `l10n_ro_anaf_d394_pos` | raportarea bonurilor în D394, inclusiv a liniilor suplimentare |

**Ce e automat:** adăugarea liniei suplimentare, calculul și consolidarea cantității, actualizarea la
schimbarea cantității, la ștergere și la retur.

**Ce rămâne manual:** configurarea produselor (produs suplimentar, multiplicator, disponibilitate în
POS); prețul și taxele produsului suplimentar.

## 8. Verificări pentru consultant

- [ ] Adăugarea produsului principal adaugă automat linia suplimentară, cu cantitatea
  `cantitate × Cantitate suplimentară`.
- [ ] Mărirea cantității produsului principal mărește cantitatea liniei suplimentare.
- [ ] Două produse diferite cu același produs suplimentar dau o singură linie suplimentară, cu suma
  cantităților.
- [ ] Ștergerea produsului principal reduce sau șterge linia suplimentară.
- [ ] Anularea ferestrei de configurare/cântărire nu lasă în bon o linie suplimentară orfană.
- [ ] La retur, linia suplimentară are cantitate negativă.
- [ ] Un produs suplimentar nedisponibil în POS nu se adaugă (verificați bifa înainte de a raporta o
  problemă).

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| Linia suplimentară nu apare | Produsul suplimentar nu este disponibil în POS | Bifați disponibilitatea în POS și reîncărcați sesiunea |
| Linia suplimentară nu apare după o configurare nouă | POS-ul a fost deschis înainte de modificare | Reîncărcați pagina POS |
| Linia suplimentară are alt preț decât procentul configurat | **Procent suplimentar** nu se aplică în POS | Setați prețul dorit pe produsul suplimentar |
| Cantitate 1 deși **Cantitate suplimentară** e 0 | Valoarea 0 este tratată ca 1 | Dacă linia nu se dorește, goliți **Produs suplimentar** pe produsul principal |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului și nici test `tests/test_screenshots.py`
(testele sunt tururi POS automate, fără capturi). În `static/description/` sunt doar iconița, bannerul
și imaginea principală pentru Odoo Apps. Capturile pentru configurarea produsului și pentru coșul POS
(pașii 1–3) se pot genera ulterior cu skill-ul `fisa-screenshots`.

## 11. Observații pentru manual

- De explicat casierului că linia suplimentară nu se adaugă manual și nu trebuie ștearsă separat:
  urmează singură produsul principal.
- Disponibilitatea în POS a produsului suplimentar este cea mai frecventă cauză a „liniei care nu
  apare”.
- Diferența față de comenzile de vânzare: în POS nu se aplică **Procent suplimentar**.
