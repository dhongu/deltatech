# Ce e nou în 19.0 — Raport materiale de ambalare

## Ce e nou față de 18.0
- **Evidența materialelor de ambalare consumate pentru produsele facturate**: configurare pe produs, urmărire pe liniile de factură și asistent de completare în masă — baza pentru raportările de ambalaje.
- **Corecții manuale păstrate la validare**: cantitățile de materiale de ambalare editate sau șterse pe factură nu mai sunt rescrise la validarea acesteia — comutatorul „Actualizare automată” din tab se dezactivează singur la prima editare, iar butonul „Refresh” recalculează și readuce factura sub actualizare automată.
- **Cantitate separată la achiziție și la vânzare**: un produs ambalat într-un fel de furnizor și în alt fel la livrare are acum două coloane pe material — „Cantitate achiziție” și „Cantitate vânzare”. Facturile de la furnizor și refuzurile lor folosesc prima, facturile către client și notele de credit pe a doua; materialele cu zero pe direcția respectivă nu mai apar în raport. La upgrade, cantitatea unică existentă e copiată în ambele coloane, deci comportamentul rămâne identic până când corectați produsele ambalate diferit.
