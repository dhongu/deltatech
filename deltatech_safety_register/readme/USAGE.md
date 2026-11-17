Give the users the **Safety officer** or **Safety manager** access right (Settings → Users, category
*Human Resources*, field **Safety register**). Users who export the register also need the **Export**
right. Hours worked for LTIFR come from the **Attendances** app, so the employees must
check in and out there.

1. **Safety → Events** lists the register: reference, date, type, location, injured employee,
   commuting flag, open actions and status. Lost-time injuries and fatalities are shown in red. Use
   the filters and **Export** (XLSX) to extract the register.

   ![Safety events list with near misses, an incident, injuries and lost-time injuries, their SAF references by event year, injured employee, commuting flag, open actions and status](static/description/en/01_lista_evenimente.png)

2. **Safety → Events → New**: choose the **Type**, the **Date**, the **Location** and describe the
   event. On save it gets the reference `SAF/<event year>/NNNN` and the status **Reported**.

   ![A near miss form: reference, type Near miss, date, location and description, status Reported](static/description/en/02_near_miss.png)

3. For an injury (**Injury (no time lost)**, **Lost-time injury**, **Fatal**) set the injured person:
   **Injured employee**, **Injured partner** or **Injured person name**. The department comes from
   the employee. Tick **Commuting accident** when it happened on the way to or from work.

   ![A lost-time injury form with the injured employee, the department filled in and the Commuting accident checkbox](static/description/en/03_accident_incapacitate.png)

4. Write the **Root cause**, then add the **Corrective actions** with **Responsible** and **Deadline**.
   Each responsible receives a To-Do activity on the event. Press **Mark done** when the action is
   completed.

   ![Corrective actions tab: one action done with its done date, one open action with the Mark done button](static/description/en/04_actiuni_corective.png)

   ![Event chatter: the To-Do activity of the responsible user with the summary and deadline of the open action](static/description/en/05_activitate_responsabil.png)

5. Press **Close** once every action is done. A closed event can only be changed by a Safety
   manager and cannot be deleted.

   ![A closed event: status Closed, closed date and all corrective actions done](static/description/en/06_eveniment_inchis.png)

6. **Safety → Corrective actions** shows the open actions of all events; use **My actions** or group
   by **Responsible**.

   ![Corrective actions list filtered on Open, with event, description, responsible, deadline and Mark done](static/description/en/07_lista_actiuni.png)

7. **Safety → Reporting → Indicators**, choose the **Year**: LTIFR (lost-time injuries × 1,000,000 /
   hours worked), lost-time injuries, hours worked, commuting accidents and near misses of that
   year. Days without accident and the last injury date are counted to today, whatever the year.

   ![Safety indicators for last year: LTIFR, lost-time injuries, hours worked, commuting accidents, near misses, days without accident and last injury date](static/description/en/08_indicatori.png)

   When a month that has already started has no hours in Attendances, LTIFR is hidden and a warning
   lists the missing months.

   ![Safety indicators for the current year with the warning that hours worked are missing for 03/2026](static/description/en/09_indicatori_ore_lipsa.png)
