Nothing to do day to day: once a unit carries a code, every electronic document
built from it uses that code. The work is a one-off check of the units, at go-live.

**1. Open the list of units.** In **Invoicing → Configuration → Settings**, block
**Units & Packagings**, tick **Units of Measure & Packagings** and save; the
**Units & Packagings** link below it opens the list of units. With Sales or
Inventory installed, the same list is also in their **Configuration** menu.

![Invoicing settings scrolled to the Units & Packagings block: Units of Measure & Packagings is ticked (1) and the Units & Packagings link (2) opens the list of units](static/description/en/01_setare_unitati_ambalaje.png)

**2. Find the right code.** The nomenclature is in **Settings → UNECE Codes**, a
menu of its own in the Settings top bar. **Code** is the value sent in the XML,
**Source** tells a unit of measure (Rec 20) from a packaging (Rec 21, codes
prefixed with `X`). Use **Packaging (Rec 21)** for units that pack a quantity
(box `XBX`, bag `XBG`, pallet `XPX`; search by code or by the ANAF name) and **Units (Rec 20)** for actual units of
measure (`KGM`, `MTR`, `MTK`).

![UNECE Codes list opened from the Settings top bar (1), filtered on Packaging (Rec 21) (2): 377 codes with their Code, Name and Source, such as X4A Box, steel and X4H Box, plastic](static/description/en/02_coduri_unece_ambalaje.png)

**3. Check the units.** In the units list, show the optional **UNECE Code**
column from the optional-columns icon at the right of the header. Every unit of
your own needs a code. An empty cell means Odoo's built-in mapping applies —
`C62` (one piece) for any unit the standard does not recognise. Square metres and
millilitres already carry `MTK` and `MLT`, set by the module on install.

![Units & Packagings list with the UNECE Code column shown: m² has MTK - square metre, ml has MLT - millilitre and the custom unit Box of 13 kg has XBX - Box (1); standard units such as Units, kg or L are left empty](static/description/en/03_unitati_coloana_cod_unece.png)

**4. Set the code on the unit.** Open the unit and pick the value in **UNECE
Code**. Nothing changes on products or invoices.

![Form of the unit Box of 13 kg, 13 kg, with UNECE Code (1) set to XBX - Box](static/description/en/04_unitate_cutie_cod_unece.png)

**5. Invoice as usual.** Without the Sales app, the **Quantity** and **Unit**
columns of invoice lines are hidden by default; show them from the
optional-columns icon of the lines. In the e-invoice XML, the line's
`cbc:InvoicedQuantity` now carries `unitCode="XBX"` instead of `C62`.

![Posted customer invoice INV/2026/00001: the line is 10.00 of Box of 13 kg (1) at 245.00, VAT 21%](static/description/en/05_factura_unitate_cutie.png)

```xml
<cbc:InvoicedQuantity unitCode="XBX">10.0</cbc:InvoicedQuantity>
```

The code applies to both paths that build electronic documents: eTransport,
through `uom.uom._get_unece_code()`, and UBL/CII invoices (CIUS-RO included),
which reach the same value through a separate method of their own.
