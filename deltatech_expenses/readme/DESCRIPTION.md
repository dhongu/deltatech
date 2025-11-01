Features:

- Introducerea decontului de cheltuieli într-un document distinct care generează automat chitanțe de achiziție
- Validarea documentului duce la generarea notelor contabile de avans și înregistrarea plăților

Configurare:
- În registrul de numerar trebuie completat câmpul "Cash advances" cu 542.


# Exemplu de Testare: Decontarea Cheltuielilor din Avans

## 🎯 Obiectivul Testului
Decontarea corectă a unui avans de **1.000 RON**, cu cheltuieli totale de **800 RON**, rezultând în **restituirea diferenței** de **200 RON** de către angajat.

## ⚙️ Pașii de Testare (Scenariu)

| Pas | Acțiune Utilizator (Tester) | Rezultat Așteptat (Verificare) |
|---|---|---|
| **1. Acordare Avans** | Se înregistrează acordarea unui avans de 1.000 RON angajatului X. | Soldul contului **542** (Avansuri de decontat) crește cu 1.000 RON. |
| **2. Creare Decont** | Angajatul X inițiază un nou decont, făcând referire la avansul primit. | Decontul preia automat valoarea avansului de 1.000 RON. |
| **3. Introducere Cheltuieli** | Se introduc cheltuielile: Cazare (500 RON, TVA inclus) și Transport (300 RON, TVA inclus). | Total cheltuieli = **800 RON**. Se calculează corect TVA-ul deductibil. |
| **4. Validare Calcul** | Se verifică automat calculul diferenței. | **Avans (1.000) - Cheltuieli (800) = Diferență de restituit (200 RON)**. |
| **5. Aprobare Decont** | Decontul este trimis și aprobat de toți factorii decizionali. | Statutul decontului se schimbă în "**Aprobat/Decontat**". |
| **6. Restituire Avans** | Angajatul restituie diferența de 200 RON (înregistrare la Casierie/Bancă). | Se generează documentul de încasare (Chitanță/Dispoziție de Încasare). |
| **7. Contabilizare Finală** | Sistemul contabilizează decontul și restituirea. | Contul **542** al angajatului se închide (Sold **0**). |

---

## 📝 Note Contabile Aferente

Acestea sunt notele contabile așteptate pentru a testa închiderea corectă a avansului (Contul 542 - Avansuri de decontat):

| Nr. Crt. | Operațiune | Cont Debitor | Cont Creditor | Suma (RON) | Explicație |
|---|---|---|---|---|---|
| **1** | Acordare Avans | **542** (Avans X) | **5311/5121** (Casa/Banca) | 1.000 | Acordarea avansului. |
| **2** | Decontare Cheltuieli | **6xx** (Cheltuieli) | **542** (Avans X) | 672.27 | Valoarea cheltuielilor fără TVA (ex: 800 - 127.73). |
| | | **4426** (TVA Deductibil) | **542** (Avans X) | 127.73 | TVA aferent cheltuielilor (ex: 19%). |
| **3** | Restituire Sold | **5311/5121** (Casa/Banca) | **542** (Avans X) | 200 | Diferența restituită de angajat. |

**Verificare Sold Final Cont 542 (Avans X):**
* **Total Debitor:** 1.000 RON
* **Total Creditor:** 800 RON (Cheltuieli) + 200 RON (Restituire) = 1.000 RON
* **Sold Final:** 1.000 (D) - 1.000 (C) = **0 RON (Corect)**
