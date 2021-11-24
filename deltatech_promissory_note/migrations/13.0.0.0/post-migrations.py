def migrate(cr, version):
    cr.execute(
        """
        update promissory_note as pn
            set invoice_id = (select id from account_move as am where am.old_invoice_id = pn.old_invoice_id );
    """
    )
