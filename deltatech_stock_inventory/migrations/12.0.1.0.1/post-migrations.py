# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    cr.execute(
        """
             insert into product_warehouse_location
              ( product_id, warehouse_id, loc_rack, loc_row, loc_case)
               select  id as product_id, 1, loc_rack, loc_row, loc_case
                from product_template
    """
    )
