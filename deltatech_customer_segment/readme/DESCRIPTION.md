Every night the module computes, for each customer and company, where the
customer stands in the sales portfolio:

- **buying rhythm**: the average number of days between purchases, measured
  on the customer's own history, and how many days he has been silent;
- **rhythm segment**: new, active, at risk, dormant or lost, judged against
  the customer's own rhythm and not against a company average. A weekly buyer
  silent for three weeks is at risk; a quarterly buyer silent for two months
  is still active;
- **sales**: lifetime, last 12 months, current period against the previous
  one, average purchase, growth;
- **receivables**: open balance, overdue amount, number of overdue invoices
  and the age of the oldest one, read only from customer invoices;
- **portfolio classification**: top customer, growing, high potential, small
  orders (upsell), stable, declining, inactive (three levels) or payment
  risk, plus a risk score and a potential score.

The data comes from posted customer invoices (credit notes deducted) or from
confirmed sales orders, untaxed and in company currency. Sales of the
contacts roll up to their company. No field is added on the partner: the
results live in their own table, one row per customer and company, and are
opened from the partner form (*Action > Customer Segment*) or from
*Sales > Customer Portfolio > Customer Segments*.

Salespeople with the *Own customers* role see only the customers they are the
salesperson of; the *All customers* role sees every customer and edits the
thresholds.

The engine is the base of the customer analysis dashboard and of the weekly
sales missions.
