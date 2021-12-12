# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    if not version:
        return
    # try:
    #     cr.execute("insert into date_range_type (id, name) values (1, 'lunar');")
    #     cr.execute(
    #         """
    #         insert into date_range
    #          (id, name, date_start, date_end, type_id)
    #         select id, name, date_start, date_stop, 1 from account_period;
    #         """
    #     )
    # except Exception:
    #     pass
