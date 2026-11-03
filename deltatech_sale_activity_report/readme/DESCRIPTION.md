Keeps a journal of who worked on which sales order and when, so a sales manager can see the activity
of each salesperson per day.

**One activity record per order, user and day.** The first time an internal user touches a sales order
on a given day, an activity record is created for that order, user and date; later actions of the same
user on the same day are added to it. Actions of the system and of portal or website users are not
recorded.

**What is recorded.** The *Log* tab of a record holds the timed list of:

- field changes, with the old and the new value (order lines are described line by line);
- the *Confirm*, *Cancel*, *Set to Quotation*, *Lock*, *Unlock* and *Send* buttons;
- messages posted in the chatter.

Scheduling an activity on the order also creates the record of the day, without a log line. The record
keeps the order status, and the flags *Chatter Message* and *Tags Changed*. Binary fields (labels,
signatures) are not logged, and long values are truncated.

**Activity Records report.** *Sales > Reporting > Activity Records* opens the records of the current
month in list, form, pivot (users and stages per day) and graph views, with *Today*, *Yesterday*,
*This Month* and *This Year* filters and grouping by user, stage or date.

**Access.** *User: Own Documents Only* salespeople can read the records of their own orders and of
unassigned ones; *User: All Documents* and *Administrator* see all of them, within their allowed
companies. Only the Sales *Administrator* can change or delete records. The *Reporting* menu of Sales,
and so the report, is shown to the Sales *Administrator* only.

**Automatic clean-up.** A *Data Cleaning* rule deletes the records older than 2 months. The period can
be changed in *Data Cleaning > Configuration > Rules > Recycle Records*, rule *Sale Order Activity
Record*.

**With order stages.** When the order stages from `deltatech_website_sale_status` are installed, the
record also keeps the order stage and the *AWB Generated* flag, set when the order moves to *Pre
advice*.
