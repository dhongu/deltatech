Features:

- caclul cost mediu ponderat pe aria de evaluare si cont pentru fiecare produs
- caclulul evaluarii unui produs se face din notele contabile
- se definiesc care sunt conturile utilizte la evaluarea produselor



pentru inializare e necesar o actiune server cu urmatorul cod

```python
env["product.valuation"].recompute_all_amount()
env["product.valuation.history"].recompute_all_amount()
```
