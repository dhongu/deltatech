Map sheets and route logs are managed by a **Fleet Administrator**; a **Fleet Officer** can record
fuel logs. Before you start, fill in on the vehicle the **Average Consumption** (l/100 km, used for
the normal consumption of the routes), the **Reservoir capacity**, the vehicle category and the fuel
cards, and create the locations and the routes between them (**Fleet → Fleet → Master data**).

1. **Record the fuel logs** — **Fleet → Fleet → Vehicles Fuel Logs**, **New**. Fill in the vehicle,
   the **Date Time**, the card, the liters, the price per liter and the amount (any two compute the
   third), **To full**, the fuel and the odometer. Optionally link the map sheet; only the sheets of
   the vehicle that include the date are proposed. The odometer becomes an odometer reading of the
   vehicle.

   ![Fuel log of vehicle Dacia/Logan/B-101-TRB: Date Time (1), Liter 40 (2), Map Sheet MS/00010 (3) and the odometer 45,000 (4)](static/description/en/01_alimentare.png)

2. **Create the map sheet** — **Fleet → Fleet → Map Sheets**, **New** (or the **Map Sheets** button on
   the vehicle). The number is given automatically. Choose the vehicle (the drivers, the category
   and the average consumption are filled in), then the **Date Start** and **Date End**. **Odometer
   Start** and **Odometer End** are read from the odometer readings of the vehicle or written by hand;
   the **Read odometer** buttons repeat the reading while the sheet is in **Draft**.

   ![Draft map sheet: Vehicle (1), Date Start (2), Date End (3), Odometer Start with Read odometer start (4) and Odometer End with Read odometer end (5)](static/description/en/02_foaie_parcurs.png)

3. **Add the route logs** — in the **Route Log** tab, add one line per trip: choosing the route fills
   in the distance and the end time. Route logs recorded separately (**Fleet → Fleet → Route Log**)
   for the vehicle and the period are brought in with **Get route log**.

   ![Route Log tab: the Get route log button (1), the route (2) and the distance (3) of the first line, total 240 km](static/description/en/03_traseu_parcurs.png)

4. **Add the fuel logs** — in the **Fuel Logs** tab, add the fuel logs directly, or bring the ones of
   the vehicle and the period with **Get fuel log**.

   ![Fuel Logs tab: the Get fuel log button (1), the liters (2) and the amount (3) of the fuel log](static/description/en/04_alimentari_foaie.png)

5. **Check the sheet** — the header shows **Total distance**, **Total Liter**, **Total Amount**,
   **Normal Consumption** (distance × average consumption / 100) and the computed reservoir level at
   the start and at the end. **Odometer End** − **Odometer Start** should equal **Total distance**,
   and the end level should be about the start level + liters − normal consumption.

   ![Map sheet header: Total distance 240 (1), Total Liter 40 (2), Normal Consumption 15.60 (3), Level Reservoir Start 9 (4) and Level Reservoir End 33.40 (5)](static/description/en/05_verificare_foaie.png)

   Print the sheet from **Print → Map Sheet**: the PDF contains the header, the route logs and the
   fuel logs.

   ![Map Sheet PDF with the header, the Route log table (240 km, 15.6 l) and the Fuel log table (40 l, 288 lei)](static/description/en/06_foaie_parcurs_pdf.png)

6. **Confirm and close the sheet** — **Confirm** moves the sheet to **In Progress**; **Done** closes
   it and marks its fuel logs as done. A sheet with a total distance of zero cannot be closed.
   Duplicating a sheet creates the sheet of the next day.

   ![Map sheet In Progress (2) with the Done button (1)](static/description/en/07_confirmare_foaie.png)

7. **Cost per kilometer** — **Fleet → Reporting → Distance Report** (Fleet Administrator) asks for
   the **Start Date** and **End Date** (the current month by default). **Show Report** lists, per
   vehicle, the **Cost** (services and contracts of the vehicle, fuel logs included), the
   **Distance** (from the odometer readings at the ends of the period) and the **Price** per km.
   The distance goes from the reading before the period (or the first one in it) to the reading
   after the period (or the last one in it); with a single reading, the distance and the price are
   zero.

   ![Distance Report window: Start Date (1), End Date (2) and Show Report (3)](static/description/en/08_raport_cost_km_perioada.png)

   ![Distance Report list for October 2026: Dacia/Logan/B-101-TRB with Cost 288 (1), Distance 240 (2) and Price 1.20 (3)](static/description/en/09_raport_cost_km.png)
