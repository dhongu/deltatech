1. Go to **Manufacturing > Configuration > Settings**, section *Operations*:
   - **Partial Substitution** (on by default): a component may be split between the
     original product and its alternatives. When off, an alternative is used only if it
     covers the whole shortage.
   - **Substitute on Availability Check** (on by default): the automatic substitution
     runs again on *Check Availability*, not only at confirmation.
2. Open a bill of materials. On each component line, the **exchange** button opens the
   alternatives of the line:
   - set **Substitution** to *Manual* or *Automatic*;
   - add the alternative components, in order of preference, with the quantity that
     replaces the quantity of the original component on the line, and optionally a
     validity period and a note.
3. All the alternatives can also be reviewed in **Manufacturing > Products > BoM
   Alternatives**.
