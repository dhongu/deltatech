# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


def migrate(cr, version):

    cr.execute("UPDATE product_template SET search_index = upper(search_index)")
    cr.execute(
        """
            CREATE INDEX product_template_search_index_gin
                ON product_template
                USING gin(search_index gin_trgm_ops);
    """
    )
    cr.execute(
        """
            CREATE INDEX product_alternative_name_gin
                ON product_alternative
                USING gin(name gin_trgm_ops);
        """
    )
