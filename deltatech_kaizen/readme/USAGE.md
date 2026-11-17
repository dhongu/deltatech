Kaizen projects follow a fixed flow: Draft → Analysis → Actions → Verification → Done.

1. Go to **Kaizen → Projects**. The list opens on the **Open** filter, with the loss type, responsible, deadline, baseline loss, current loss, monthly savings and state of each project.

   ![Kaizen Projects list with the Open filter: two projects in the Actions state, with baseline loss, current loss and monthly savings](static/description/en/01_lista_proiecte.png)

2. Click **New**, enter the project name, **Loss Type**, **Responsible**, **Start Date** and **Deadline**. On save the project gets a `KZN/` reference. In the **Baseline and Results** tab, enter the **Baseline Date** and the **Baseline Loss / Month**, and optionally the **Target Loss / Month**. Savings stay at zero until a measurement after the fix is recorded. Click **Start analysis**.

   ![Project in Draft: Baseline and Results tab with the baseline loss of 12,000.00 per month, the target and savings still at zero](static/description/en/02_proiect_linie_baza.png)

3. In the **5 Why** tab, add up to five lines, each answering "why?" for the line above, and tick **Root Cause** on the line where the analysis stops. Only one line can be the root cause.

   ![5 Why tab: five lines, the last one about the missing preventive maintenance plan is marked as root cause](static/description/en/03_analiza_5_de_ce.png)

4. In the **Ishikawa** tab, add the possible causes, each with a **Category** (Man, Machine, Method, Material, Measurement, Environment). Click **Start actions**.

   ![Ishikawa tab: one cause in each of the six categories](static/description/en/04_analiza_ishikawa.png)

5. In the **Actions** tab, add each corrective action with a **Responsible** and a **Deadline**. Click the **Done** button on the line when the action is finished: **Done On** gets today's date. Overdue open actions are shown in red, finished ones in green.

   ![Actions tab: a finished action in green, an overdue one in red and one within its deadline](static/description/en/05_actiuni.png)

6. When every action is done, click **Start verification**. Enter the **Measured Date** and the **Current Loss / Month** measured after the fix. **Monthly Savings** is the baseline loss minus the current loss, **Annual Savings (projection)** is the monthly savings × 12, and **Target Reached** is ticked when a target is set and the measured current loss is at or below it.

   ![Project in Verification: current loss 3,500.00, monthly savings 8,500.00, annual projection 102,000.00 and Target Reached ticked](static/description/en/06_verificare_economii.png)

7. A Kaizen manager clicks **Close project**. Closing is refused without a root cause, with open actions, with a zero baseline or without a measured date. The state becomes **Done** and **Closed On** is set. **Cancel**, also manager-only, stops a project in any state except Done.

   ![Closed project in the Done state, with the Closed On date](static/description/en/07_proiect_inchis.png)

8. **Kaizen → Ishikawa** lists the causes of all projects, grouped by category.

   ![Ishikawa Causes list grouped by category, with the project and the cause on each line](static/description/en/08_cauze_ishikawa_grupate.png)

9. **Kaizen → Actions** lists the actions of all projects, with overdue ones in red: the follow-up list for the weekly improvement meeting.

   ![Kaizen Actions list: the actions of both projects, the overdue one in red](static/description/en/09_lista_actiuni.png)
