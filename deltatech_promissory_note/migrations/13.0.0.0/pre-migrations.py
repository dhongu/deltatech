def migrate(cr, version):
    cr.execute(
        """
        ALTER TABLE promissory_note DROP CONSTRAINT promissory_note_invoice_id_fkey;
        ALTER TABLE promissory_note
                ADD COLUMN old_invoice_id integer;
        update promissory_note set old_invoice_id = invoice_id where old_invoice_id is null;
        update promissory_note set invoice_id = null where old_invoice_id is not null;
    """
    )
