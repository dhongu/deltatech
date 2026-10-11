## Public holidays

The module reads the public holidays of the company; it does not create them.

1. Go to **Settings > Technical > Resource > Working Schedules** (debug mode)
   and check that the company has a working schedule with the right working
   days.
2. Open **Settings > Technical > Resource > Resource Time Off** (or
   **Time Off > Configuration > Company Holidays** when the Time Off application
   is installed) and add the public holidays of the year, with no resource.
   A holiday linked to another working schedule or to another company is
   ignored.
3. Add the holidays of each new year before the invoices of that year fall
   due. Movable holidays (Easter, Pentecost) change every year.

For Romanian companies, the public holidays of the Labour Code (art. 139),
including the Orthodox Easter and Pentecost, can be generated for a whole year
with the wizard of the `l10n_ro_hr_pontaj` module, or entered by hand.
