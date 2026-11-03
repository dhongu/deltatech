Publish the payment providers and the delivery methods used on the shop first
(**Website → Configuration → eCommerce → Payment Providers** and **Delivery Methods**). The rules
below only hide options; they never add a provider or a delivery method that is not enabled and
published.

**Configure the rules**

1. **Payment providers allowed with a delivery method** — open the delivery method (e.g.
   **Curier rapid**), go to the **Payment Acquirer** tab (1) and fill in **Payments Provider Allowed**
   (2). With this delivery method the customer gets only these providers. An empty list allows all of
   them.

   ![Delivery method form, Payment Acquirer tab: Payments Provider Allowed with two providers](static/description/en/01_livrare_furnizori_permisi.png)

2. **Weight limits** — on the delivery method, next to the price, fill in the minimum and the
   maximum of **Weight limits** (highlighted), in the unit shown at the end of the row. The method is offered only when the estimated weight of the cart
   (product weight × quantity, goods only) is between them. A limit of 0 is not checked: 50 - 0 means
   "from 50 kg up".

   ![Delivery method form: Weight limits 50.00 - 0.00 kg](static/description/en/02_livrare_limite_greutate.png)

3. **Hide a delivery method for customer tags** — on the **Payment Acquirer** tab (1), fill in
   **Restrict for partners with label** (2). Customers whose **company** has one of these tags do not
   see the method.

   ![Delivery method form, Payment Acquirer tab: Restrict for partners with label with the tag Provincie](static/description/en/03_livrare_restrictie_eticheta.png)

4. **Value limit and tags of a payment provider** — open the provider, group **Restrictions**:
   **Value Limit** (1) is the order total, taxes and delivery included, above which the provider is
   no longer offered (a total equal to the limit is still allowed; the limit is compared with the total in the order currency, without
   conversion); **Restrict Label** (2) hides the
   provider from the customers on the order that have one of the tags.

   ![Payment provider form, Restrictions group: Value Limit 1,500.00 and Restrict Label](static/description/en/04_furnizor_plata_restrictii.png)

5. **Tag the customers** — on the customer (**Website → eCommerce → Customers**), fill in **Tags**
   (1).

   ![Customer form with the tag Provincie](static/description/en/05_client_etichete.png)

**Which tags are read**

For delivery methods the module reads the tags of the customer's **company** (the commercial
partner); for payment providers, the tags of the **customer on the order**. For a contact person of
a company, a tag set only on the company hides the delivery method but not the payment provider: set
it on both when both must be hidden.

**What the customer sees in the checkout**

6. **Delivery step** — the **Delivery method** list (1) shows only the methods left after the rules:
   here the cart weighs 3 kg and the customer has the tag Provincie, so the pallet transport (from
   50 kg) and the local courier (hidden for Provincie) are missing.

   ![Checkout Address step: only two delivery methods are offered](static/description/en/06_site_pas_livrare.png)

7. **Payment step with the courier** — the **Payment method** list (1) shows only the providers
   allowed with the chosen delivery method. The customer sees the **payment method** name (Card, Cash
   on Delivery), not the provider name from the backend.

   ![Checkout Payment step with the courier: Card and Cash on Delivery](static/description/en/07_site_plata_curier.png)

8. **Payment step with pickup** — with the pickup method only **Wire Transfer** is left, the only
   provider allowed on it.

   ![Checkout Payment step with the pickup method: only Wire Transfer](static/description/en/08_site_plata_ridicare.png)

9. **Above the value limit** — with 10 items the order total, taxes included (2,317.15 lei), is above the 1,500 lei
   limit of Cash on Delivery, so only **Card** is left.

   ![Checkout Payment step above the value limit: only Card](static/description/en/09_site_plata_peste_limita.png)

**Standard rules that still apply**

- Cash on Delivery is offered only by the delivery methods with the standard **Cash on Delivery**
  option, and, when the list is filled in, only if it is in **Payments Provider Allowed**.
- The standard **Maximum Amount** of a provider and **Max Weight** of a delivery method are
  applied too, next to the rules of this module.
- If the rules leave no delivery method, the shop shows "Sorry, we are unable to ship your order.";
  if they leave no payment provider, the payment step shows *No payment method available*. Keep one delivery
  method and one provider without restrictions as a fallback.

The **Logo** of the delivery method and the **Payment Provider** of the contact are not used in the
checkout.
