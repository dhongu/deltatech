Calculates packaging materials from invoiced product quantities and provides an
aggregate packaging-material report from the invoice list. Every material is configured
with a purchase quantity and a sale quantity, for the products packed one way by the
vendor and another way on shipping; vendor bills use the first, customer invoices the
second.

The materials can also be configured on the product category, as the default for
the products it holds: a product without materials of its own uses the ones of its
category, or of the closest parent category that configures some. A product that uses
no packaging material at all can stop the inheritance explicitly.

The quantities are refreshed when the invoice is posted, as long as the invoice is
under automatic update. Editing or deleting a quantity by hand takes the invoice out
of automatic update, so that the correction survives the validation of the invoice;
the Refresh button computes the quantities again and puts the invoice back under
automatic update.
