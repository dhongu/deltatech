With *Log in with Employees*, Odoo keeps **Close Register** for the managers, together with
other manager rights such as editing payments, creating products and, with *Price Control*,
changing prices. To let the cashier who worked the shift close it, you would have to give all
of them.

This module moves only the button:

- **Cashiers close their own shift**: employees with the *Cashier* role get *Close Register*
  in the menu, where a manager finds it. The closing popup is the usual one.
- **Nothing else moves**: the other manager rights stay with the managers. *Restrictive* and
  *Supervised* employees still cannot close, and a cash difference above the authorized amount still
  needs a manager.
- **Per register**: a chain keeps the closing with the shop manager where it wants to, and gives
  it to the cashiers where the shop runs on shifts.

The option is on by default: installing the module is the decision.
