1. Go to *Point of Sale > Configuration > Settings* and select the register.
2. Under *Pricing*, tick *Price Control* (restrict price modification to managers).
3. Tick *Managers included*, right below it, and save.
4. Reload the register page if a session is already open: the setting is read when
   the register loads.

![Price Control and Managers included ticked in the Pricing section of the register settings](static/description/en/01_setari_blocare_pret.png)

From now on the *Price* key of the numpad stays disabled for everybody on this
register, POS managers and employees with the *Manager* role included. *Qty* and *%* keep
working as before.

![Register with a product on the order: the Price key of the numpad is disabled for a POS manager](static/description/en/02_pos_tasta_pret_blocata.png)

To change a price, edit the *Sales Price* of the product; with *POS Price Sync* installed
the new price reaches the open registers without a reload.

![Product form with the Sales Price field, where a wrong price is corrected](static/description/en/03_corectie_pret_produs.png)
