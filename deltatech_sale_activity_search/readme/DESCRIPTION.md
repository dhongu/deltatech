Keeps on each sales order a text field with the types of its pending
activities, so that orders can be found by the kind of follow-up they wait for
(for example *Call*, *Email* or a custom activity type).

**Active Activity Types field.** The module adds the stored field *Active
Activity Types* to the sales order. It holds the names of the activity types of
the order's open activities, separated by commas.

**Kept up to date automatically.** The field is refreshed whenever an activity
is scheduled on an order, edited (several at once included), moved to another
order or another document, marked as done or cancelled.

**Searching by activity type.** The field is stored, so it can be used in a
custom filter: in **Sales > Orders > Quotations** or **Sales > Orders > Orders**,
open the filter menu of the search bar, choose **Add Custom Filter** and build a
condition on *Active Activity Types* (for example *contains* "Call").

## Limitations

- The module adds no view, filter or column: the field is reachable only through
  a custom filter, a custom group-by or an export.
- The field is filled only for activities created, changed or removed after the
  installation. Orders with activities scheduled before the installation stay
  empty until one of their activities changes.
