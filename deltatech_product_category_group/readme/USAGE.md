1. Go to **Inventory > Configuration > Product Categories**, open a
   category and set the **User Group** field to the group of users
   responsible for products in that category (and its sub-categories,
   up to 3 levels up).
2. On a transfer (**Inventory > Transfers**) that has no responsible
   user yet and is in the *Ready* state, click the **Responsible**
   button in the list view header (or run it from automated code, e.g.
   after `action_assign`).
3. The system looks at the categories of the products in the transfer,
   finds the matching user group(s), and assigns the transfer to the
   user from that group with the fewest currently "Ready" transfers
   already assigned — balancing the workload automatically.
