# Ce e nou în 19.0 — Optimizare imagini

## Funcționalități noi
- **Eliminarea fundalului din imaginile de produs.** Din lista de produse, *Acțiune → Remove Image Background* decupează produsul și îl salvează pe fundal transparent, în format WebP, inclusiv imaginile din galerie. Originalul se păstrează și se poate reface. Necesită biblioteca `rembg` pe server.
- **Eliminarea imaginilor de produs duplicate.** Sunt găsite imaginile identice octet cu octet și păstrată una singură — pe cataloagele importate din mai multe surse recuperează spațiu important, fără risc de a pierde o imagine unică.

## Îmbunătățiri
- **Avertisment explicit că opțiunea de conversie forțată la JPEG este ireversibilă** (transparența devine negru, iar imaginea originală nu mai poate fi recuperată).
