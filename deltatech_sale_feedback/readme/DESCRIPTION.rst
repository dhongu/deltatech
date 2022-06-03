Features:
 - Sends an automated e-mail to clients based on out invoices
 - A cron job (default not active) is used to send the e-mails at 3 days after the invoice date. Another interval can be set using the sale.days_request_feedback system parameter
 - E-mail template used: Invoice: request feedback

Descriere:
 - Trimite la client un email pentru a cere feedback pentru produsele vandute.
 - Trimiterea se face prin cron job (la instalare inactiv), default la 3 zile dupa data facturii. Daca se doreste alt interval, se foloseste paramentrul de sistem sale.days_request_feedback
 - Template-ul de e-mail: Invoice: request feedback
