# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
            insert into maintenance_equipment (id, name, effective_date, company_id, active)
                 select id, name, create_date, 1, true from service_equipment where base_equipment_id is null;
            update service_equipment set base_equipment_id = id where base_equipment_id is null;
        """
    )
