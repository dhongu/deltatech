18.0.0.0.15 (2026-10-07)
~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- FIX: ``_compute_is_transit_transfer`` folosea ``self.second_transfer_created``
  în loc de ``record.second_transfer_created`` în interiorul buclei ``for record
  in self:``. La citirea mai multor transferuri deodată (listă), asta arunca
  ``Expected singleton`` pe recordset-ul întreg.
