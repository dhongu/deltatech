18.0.1.2.11 (2026-10-07)
~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- FIX: ``product.supplierinfo.create`` lipsea decoratorul ``@api.model_create_multi``,
  desi semnatura (``vals_list``) astepta o lista de dict-uri. Fara decorator, ORM-ul
  nu garanteaza ca metoda primeste mereu o lista - un apel cu un singur dict ar
  ajunge direct in ``super().create()`` cu forma gresita.
