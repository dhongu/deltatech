Features:

- Adds a **Removal Priority** field to stock locations.
- Integrated with **Putaway Rules**: the removal priority can be automatically determined based on the sequence of the applicable putaway rule for a specific product and location.
- Extends the removal strategy logic: allows selecting a new removal strategy called **Priority**.
- When the **Priority** strategy is used, stock quants are removed based on their calculated priority (lower values have higher priority), followed by the location name and quant ID.
- The removal priority on quants is automatically computed and stored, taking into account:
    1. The applicable Putaway Rule sequence.
    2. The default Removal Priority defined on the Stock Location if no putaway rule applies.
- Includes configuration settings to enable or disable the Removal Priority feature globally via a security group.

