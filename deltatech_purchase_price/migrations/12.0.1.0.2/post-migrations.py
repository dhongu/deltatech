# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


# def migrate(cr, version):
#     cr.execute(
#         """
#         update product_template as pt set last_purchase_price =
#             (
#             select pph.cost
#                 from product_product as pp
#                   join  product_price_history as pph  on pph.product_id = pp.id
#
#                   where pp.product_tmpl_id = pt.id
#                   order by datetime desc, pph.id desc
#
#                   limit 1
#             )
#     """
#     )
