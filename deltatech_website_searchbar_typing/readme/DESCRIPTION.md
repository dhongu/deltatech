The placeholder of a website search box types example searches, one after another: each
example is typed letter by letter, held for a moment, erased, and the next one follows.
Visitors see at a glance what they can search for: a part code, a product name, a topic
from the user guides.

**Features:**

- Opt-in per search box: only the search forms that carry examples are animated. Installing
  the module changes nothing else on the website.
- The examples are plain text inside the search form, so they are translated with the page
  and can be edited like any other text.
- An optional prefix stays in front of every example (for instance "e.g. ").
- The animation stops for good as soon as the visitor clicks in the box or starts typing, and
  the original placeholder comes back.
- It does not run when the visitor asked the system for reduced motion
  (`prefers-reduced-motion`), and it stops if that setting is turned on during the visit.
- It waits while the browser tab is hidden or the search box is scrolled out of view.
- The search box keeps a stable accessible name: when the box has no label, the original
  placeholder is set as its `aria-label`, so screen readers do not read every changing letter.
- It works with the standard search snippet and with the `website.website_search_box_input`
  template, next to the standard autocomplete dropdown.
