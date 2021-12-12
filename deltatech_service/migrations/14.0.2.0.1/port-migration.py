# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    cr.execute(
        """
        update account_move_line as aml
        set agreement_line_id = ail.agreement_line_id
        from account_invoice_line as ail
            where aml.old_invoice_line_id = ail.id;

        update account_move_line as aml
        set agreement_id = al.agreement_id
        from service_agreement_line as al
            where al.id = aml.agreement_line_id;
    """
    )
