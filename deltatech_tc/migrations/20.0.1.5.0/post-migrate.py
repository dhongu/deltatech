def migrate(cr, version):
    """The queue cleanup runs every hour: its cron is ``noupdate``, so it is moved here."""
    if not version:
        return
    cr.execute(
        """
        UPDATE ir_cron SET interval_number = 1, interval_type = 'hours'
         WHERE id = (SELECT res_id FROM ir_model_data
                      WHERE module = 'deltatech_tc' AND name = 'ir_cron_deltatech_tc_gc_jobs')
        """
    )
