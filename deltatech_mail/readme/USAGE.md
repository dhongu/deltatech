The rules are managed by administrators, in developer mode, under **Settings → Technical → Email**.
They apply to every user and every company of the database.

1. **Substitution**: the list of the rules that change the recipients or the sender of the outgoing
   emails. An empty *Related Document Model* means every document.

   ![Substitution list: a Receiver rule for res.partner to test.mesaje@demo-mesaje.ro and a Sender rule without model, with noreply@demo-mesaje.ro](static/description/en/01_lista_substitutii.png)

2. Open or create a rule:

   - **Related Document Model**: the technical name of the model whose emails are redirected
     (`res.partner`, `account.move`...); leave it empty for every email;
   - **Substitution**: the email address to use;
   - **Type**: *Receiver* replaces all the recipients of the email and drops the CC copies, so the
     original recipients are not reached; *Sender* replaces the sender.

   Use a generic *Receiver* rule on test and training databases, so that customers and vendors do not
   receive their emails. Remove it before using the database in production.

   ![Substitution form: Related Document Model res.partner, Substitution test.mesaje@demo-mesaje.ro, Type Receiver](static/description/en/02_formular_substitutie.png)

3. **Body Substitution**: the list of the rules that replace a text in the body of posted messages.

   ![Body Substitution list with the rule Semnătură veche](static/description/en/03_lista_substitutii_corp.png)

4. Open or create a rule: the text of *Body Part* is replaced by the text of *Substitution* in every
   message posted from the chatter. Messages already posted are not changed.

   ![Body Substitution form: Body Part Echipa Vânzări, Substitution Echipa Demo Mesaje SRL – vanzari@demo-mesaje.ro](static/description/en/04_formular_substitutie_corp.png)

5. **Company email as sender**: set the system parameter `mail.use_company_email` to `True`
   (**Settings → Technical → Parameters → System Parameters**). Posted messages and queued emails are
   then sent from the email address of the author's company; an explicit sender (incoming email,
   template) is kept. The company must have an email address, otherwise posting a message is refused.

   ![System parameter mail.use_company_email with value True](static/description/en/05_parametru_email_companie.png)

Only administrators (*Administration: Settings*) can create or change the rules; internal users can
only read them.
