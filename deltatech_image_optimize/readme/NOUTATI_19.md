# Ce e nou în 19.0 — Optimizare imagini

## Funcționalități noi
- **Eliminarea fundalului din imaginile de produs.** Din lista de produse, *Acțiune → Remove Image Background* decupează produsul și îl salvează pe fundal transparent, în format WebP, inclusiv imaginile din galerie. Un wizard arată fiecare imagine înainte și după, ca rezultatul să fie verificat înainte de aplicare; originalul nu se păstrează. Fotografiile pe fundal real necesită biblioteca `rembg` pe server.
- **Eliminarea imaginilor de produs duplicate.** Sunt găsite imaginile identice octet cu octet și păstrată una singură — pe cataloagele importate din mai multe surse recuperează spațiu important, fără risc de a pierde o imagine unică.

## Îmbunătățiri
- **Decupare mai bună pe fundal alb.** Fotografiile pe fundal uniform se decupează după culoare, fără model AI: accesoriile de lângă produs (de exemplu pâlnia de lângă flacon) rămân întregi, iar urmele rămase în jurul produsului se elimină. Imaginile la care modelul AI a pierdut o parte din produs sunt semnalate și debifate. În wizard se pot schimba metoda și modelul, cu regenerarea previzualizării.
- **Avertisment explicit că opțiunea de conversie forțată la JPEG este ireversibilă** (transparența devine negru, iar imaginea originală nu mai poate fi recuperată).
