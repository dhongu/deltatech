A location ends up with negative stock, for example after sales from the showroom:

![](static/description/negative-stock.png)

1. Create an internal transfer, with the location to refill as **Destination Location** and the
   location to take the goods from as **Source Location**.

![](static/description/picking1.png)

2. While the transfer is in **Draft**, click **Get negative products**.

![](static/description/picking2.png)

3. A line is added for every product with negative stock in the destination location, with the
   quantity that brings it back to zero.

![](static/description/picking3.png)

4. Adjust the lines if needed, then confirm and validate the transfer as usual.

Each click adds the lines again, so click once per transfer. The button looks at the
destination location itself, not at its sub-locations.
