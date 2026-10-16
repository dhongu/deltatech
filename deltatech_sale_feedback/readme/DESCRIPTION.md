Features:

- Sends an automated e-mail to clients based on out invoices, asking them to rate each invoiced product
- A cron job (default not active) is used to send the e-mails at 3 days after the invoice date, only for the companies
  where *Email feedback after sale* is enabled in the Sales settings. Another interval can be set using the
  sale.days_request_feedback system parameter
- E-mail template: the one selected in the Sales settings, by default *Invoice: request feedback*
- The rating links point to the company website, when it is set
- The *Request feedback* action on invoices sends the e-mail manually

Descriere:

- Trimite la client un email pentru a cere feedback pentru produsele vândute.
- Trimiterea se face prin cron job (la instalare inactiv), default la 3 zile după data facturii, doar pentru companiile
  care au bifat *Email feedback after sale* în setările de vânzări. Dacă se dorește alt interval, se folosește
  parametrul de sistem sale.days_request_feedback
- Template-ul de e-mail: cel ales în setările de vânzări, implicit *Invoice: request feedback*
- Linkurile de evaluare duc pe website-ul companiei, dacă e completat
- Acțiunea *Request feedback* de pe facturi trimite emailul manual
