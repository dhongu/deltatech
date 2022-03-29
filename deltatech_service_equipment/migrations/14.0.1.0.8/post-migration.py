# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """

            update service_equipment as e set installation_date = sh.date
            from service_history as sh
            where state = 'installed' and sh.equipment_id =  e.id and sh.name = 'Instalare'

        """
    )
