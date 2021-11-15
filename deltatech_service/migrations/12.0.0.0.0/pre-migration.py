# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    if not version:
        return

    # cr.execute("insert into date_range_type (id, name) values (1, 'lunar');")
    # cr.execute(
    #     """
    #     insert into date_range
    #      (id, name, date_start, date_end, type_id)
    #     select id, name, date_start, date_stop, 1 from account_period;
    #     """
    # )

    # cr.execute(
    #     """
    #      -- trecere de la service_equipment_category la maintenance_equipment_category
    #      insert into maintenance_equipment_category (id, name, alias_id)
    #         select id, name, 1 from service_equipment_category;
    #
    #
    #     insert into maintenance_equipment (id, name, effective_date, company_id, active)
    #     select id, name, create_date, 1, true from service_equipment where base_equipment_id is null;
    #
    #     update service_equipment set base_equipment_id = id where base_equipment_id is null;
    #         """
    # )
