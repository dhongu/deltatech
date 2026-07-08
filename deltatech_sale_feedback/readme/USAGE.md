1. Go to **Sales > Configuration > Settings**, find the **Request feedback** setting (in the Invoicing section) and enable it.
2. Once enabled, pick the e-mail template to use (defaults to **Invoice: request feedback**).
3. By default, feedback requests are sent automatically 3 days after the invoice date by a daily cron job (**Request Feedback**, inactive by default — enable it under Settings > Technical > Automation > Scheduled Actions). To use a different delay, set the system parameter `sale.days_request_feedback` (Settings > Technical > Parameters > System Parameters) to the desired number of days.
4. To send a feedback request immediately for a specific invoice, open a customer invoice and use the **Request feedback** action (Action menu / gear icon on the invoice list or form).
