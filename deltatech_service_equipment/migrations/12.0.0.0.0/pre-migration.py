# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
         -- trecere de la service_equipment_category la maintenance_equipment_category
         insert into maintenance_equipment_category (id, name, alias_id)
            select id, name, 1 from service_equipment_category;




        """
    )
