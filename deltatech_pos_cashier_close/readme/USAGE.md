1. Go to *Point of Sale > Configuration > Settings* and select the register.
2. Under *PoS Interface*, enable *Log in with Employees*, save, and set which employees have
   *Advanced rights*, *Basic rights* and *Minimal rights*.
3. *Cashiers Close the Register*, next to it, is ticked. Untick it on the registers where the
   closing stays with the manager, and save.
4. Reload the register page if a session is already open: the setting is read when the
   register loads.

![Log in with Employees with the employees split by rights, and Cashiers Close the Register ticked](static/description/en/01_setari_casierii_inchid_casa.png)

An employee with basic rights now opens the menu and finds *Close Register*.

![Register menu of a cashier with basic rights, with Close Register](static/description/en/02_pos_meniu_casier.png)

The closing popup is the usual one. With *Set Maximum Difference*, a cash difference above the
*Authorized Difference* still needs a manager to close.

![The usual closing popup, opened by the cashier](static/description/en/03_pos_inchidere_casa.png)

Employees with minimal rights still do not get *Close Register*.

![Register menu of an employee with minimal rights, without Close Register](static/description/en/04_pos_meniu_drepturi_minime.png)
