# Fișă Modul: Capturile automate ale fișelor consultant

**Modul:** `deltatech_doc_screenshots`
**Utilizator principal:** Dezvoltator sau consultant care pregătește fișele și USAGE.md ale modulelor
**Prioritate:** 🟢 Scăzută (unealtă de dezvoltare, fără funcție de business și fără ecrane proprii)

---

## 1. Scop business

Fișele consultant și paginile de pe Odoo Apps au nevoie de capturi de ecran actuale, identice la
fiecare regenerare. Modulul face aceste capturi automat, dintr-un test al modulului documentat: testul
creează datele demo, deschide ecranele într-un browser și salvează imaginile cu numele din fișă.

- capturile în **română** sunt pentru fișa consultant (`readme/FISA_CONSULTANT.md`);
- capturile în **engleză**, din aceleași ecrane, sunt pentru `readme/USAGE.md`, publicat pe Odoo Apps.

Modulul nu adaugă meniuri, câmpuri sau ecrane în Odoo. Nu se instalează la clienți.

## 2. Bază legală și context

Fără implicații contabile sau fiscale. Context: documentarea modulelor Terrabit. Capturile se fac pe o
companie demo („RO Company”, în RON), niciodată pe datele unui client.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Dezvoltator | scrie testul de capturi al modulului documentat și îl rulează |
| Consultant | verifică pe capturi că ecranele arată fluxul din fișă |
| CI (Mentor) | regenerează capturile modulelor schimbate într-un PR |

## 4. Conturi și date implicate

Nu folosește conturi contabile. Datele de pe capturi le creează testul modulului documentat, pe
compania demo pregătită de modul (țara România, RON, limba română, drepturi contabile pentru admin).

## 5. Configurare inițială

1. În mediul Python al Odoo: `pip install playwright websocket-client pillow`, apoi
   `playwright install chrome`.
2. Modulul documentat are `tests/test_screenshots.py`, care pornește de la `ScreenshotCase`.
   Modulul de capturi nu se pune în `depends`; se instalează doar la rulare.

## 6. Flux de utilizare

### Pasul 1 — Lista capturilor

În testul modulului documentat se trece, în ordinea pașilor din fișă, câte o captură pentru fiecare
ecran: adresa ecranului, numele fișierului (`01_...png`, `02_...png`) și, opțional, butoanele sau
câmpurile de evidențiat cu contur portocaliu și număr ①②③.

### Pasul 2 — Generarea capturilor

```bash
./odoo/odoo-bin -c odoo.conf -d <baza> -i <modul>,deltatech_doc_screenshots \
    --test-tags=fise_screenshots --stop-after-init --http-port=<port liber>
```

Rezultatul:

- capturile RO în `<modul>/static/description/` (la modulele nemigrate, `readme/screenshots/`);
- capturile EN în `<modul>/static/description/en/`, cu aceleași nume, dacă testul le cere
  (`lang="en_US"`).

Capturile se generează doar la cerere (tag-ul `fise_screenshots`); o rulare obișnuită a testelor le
sare, ca să nu rescrie imaginile.

### Pasul 3 — Verificarea capturilor

Se deschide fiecare imagine și se verifică: ecranul e cel din pasul fișei, datele promise apar pe
ecran, interfața e în limba potrivită, câmpurile evidențiate au eticheta lor.

### Note de monografie și raportare

Nu generează note contabile.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `web` | singura dependență |
| `l10n_ro_doc_screenshots` (suita l10n_ro_ent) | vechiul loc al uneltei; acum doar o reexportă, ca testele existente să meargă |
| modulele cu `tests/test_screenshots.py` | consumatorii: fiecare își descrie capturile |

**Ce e automat:** pregătirea companiei demo, limba, tema luminoasă, navigarea, evidențierile, decuparea
marginilor, folderul pe limbă.
**Ce rămâne manual:** lista capturilor din test, datele demo ale fluxului și verificarea vizuală.

## 8. Verificări pentru consultant

- [ ] Rularea cu `--test-tags=fise_screenshots` produce câte o imagine pentru fiecare pas din fișă,
      cu numele din fișă.
- [ ] Capturile RO au interfața în română, cu diacritice; cele din `en/` au interfața în engleză.
- [ ] Fără `playwright` instalat, testele de capturi sunt sărite, nu picate.
- [ ] O rulare obișnuită a testelor modulului nu modifică imaginile.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| „playwright nu este instalat” (test sărit) | lipsește pachetul Python | `pip install playwright websocket-client` și `playwright install chrome` |
| „Capturile se generează doar la cerere” (test sărit) | rularea nu a cerut capturile | adăugați `--test-tags=fise_screenshots` |
| „Captura '…' a eșuat: Timeout …” | ecranul nu s-a încărcat sau selectorul nu există | citiți erorile JS din mesaj; verificați adresa și selectorul capturii |
| „HTTP 403 la /report/html/…” | raportul nu vede compania demo | lăsați implicit parametrul `companies` al capturii de raport |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are ecrane proprii, deci nici capturi ale fluxului. În
`static/description/` sunt doar iconița și imaginea principală pentru Odoo Apps. Exemple de capturi
produse de modul se găsesc în fișele modulelor care îl folosesc (ex. `deltatech_product_attribute_role`).

## 11. Observații pentru manual

- Modulul nu apare în manualul utilizatorului final: e o unealtă internă de documentare.
- Pe capturile EN, datele demo (parteneri, produse, „RO Company”, RON) rămân în română; doar interfața
  se traduce.
