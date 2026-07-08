This module works automatically once installed: every time a user changes a sale order (stage, state, tags, AWB generated, chatter messages, etc.), an activity record is logged in the background — no action needed to start tracking.

1. Go to **Sales > Reporting > Activity Records** to browse the logged changes (list, form, pivot and graph views are available).
2. Use the pivot view (rows: user and stage, columns: change date by day) to see activity volume per salesperson over time.
3. Filters/group-by are available for Today, Yesterday, This Month, This Year, and grouping by User, Stage or Date.
4. Records older than 2 months are deleted automatically by the **Data Recycle** cron job that ships with this module — no manual cleanup needed.
