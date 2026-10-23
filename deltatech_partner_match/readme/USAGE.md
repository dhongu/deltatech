For developers. Add `deltatech_partner_match` to `depends`, then:

```python
from odoo.addons.deltatech_partner_match.tools import partner_match as pm

pm.normalize_name("S.C. Popescu Ion S.R.L.")  # "ion popescu"
pm.normalize_vat("RO 012.345")  # "12345"
pm.check_vat("RO18547290")  # True
pm.normalize_phone("0722 123 456")  # "+40722123456"
pm.phone_key("+40 722 123 456")  # "722123456"
pm.name_similarity("Ana Popescu", "Ion Popescu")  # 0.67

candidates = self.env["res.partner"]._find_similar_partners(
    {"name": "Ion Popescu", "phone": "0722 123 456", "email": "ion@example.com", "city": "Cluj"},
    domain=[("is_company", "=", False)],
)
# [{"partner": res.partner(42,), "score": 0.94, "name_score": 1.0, "reasons": ["phone"]}, ...]
```
