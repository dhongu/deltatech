Modulul nu adaugă ecrane proprii: doar pune câmpurile la dispoziție. Pe formularul facturii le
afișează modulul care tipărește bonul din factură (`deltatech_sale_store`). Pe comanda POS,
`deltatech_pos` le completează fără să le afișeze; le citiți cu **Acțiuni → Export**.

**Bon simulat** (`fiscal_simulated`) este bifat de driverul casei de marcat când bonul a fost tipărit
pe o casă simulată: emulatorul din Odoo sau Terrabit Connect în mod simulat (stația are panglica
**Simulare**, vezi `deltatech_tc`). Un astfel de bon nu este document fiscal, chiar dacă are
completate numerele BF, NR și Z. Îl completează POS-ul (`deltatech_pos`) și tipărirea din magazin
(`deltatech_sale_store`); `l10n_ro_pos_fiscal_compliance_ecr` lasă astfel de bonuri în afara raportului Z
și a jurnalului AMEF.

**Ca să scrieți în ele** (un driver de casă de marcat), moșteniți mixinul pe modelul dumneavoastră:

```python
class MyModel(models.Model):
    _name = "my.model"
    _inherit = ["my.model", "deltatech.ecr.fiscal.mixin"]
```

**Ca să le citiți**, e suficient să declarați `deltatech_ecr_fiscal` în `depends`; modulele de casă
de marcat nu sunt necesare.
