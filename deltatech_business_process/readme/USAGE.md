Before you start, set up access rights and master data as described in *Configuration*.

The screenshots below were taken on demo data (project *Odoo Mobila Nord*) with a Romanian user interface.

## Project lifecycle

**Step 1 — Create the project**

Go to *Business process → Business process → Projects* and click **New**. Fill in the name, customer, project manager, start date and go-live date. The code (`P00001`) is assigned automatically. Move the project through its stages (*Preparation → Exploration → Realization → Launch → In operation → Closed*) by clicking the status bar.

![Projects list](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_projects_list.png)

The buttons at the top right open the project's processes, steps, developments, documents and issues. **Get Duration** recalculates the *Total project duration*. Only a Process admin can change the project.

![Project form](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_project_form.png)

**Step 2 — Add processes and their steps**

Go to *Business process → Business process → Processes* and click **New** (or use the *Processes* button on the project, which fills in the project for you). *Name*, *Project* and *Area* are required. You can type a code (for example VZ02); otherwise it is assigned automatically.

![Processes list, grouped by area](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_processes_list.png)

On the **Process steps** tab add the steps in order, each with a *Step responsible*. Steps can be edited only while the process is in *Draft* or *Design*.

![Process and its steps](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_process_steps.png)

On the **Duration** tab enter the effort estimates (configuration, training, data migration, testing) and the design (BBP) period. The process total is the sum of the four estimates.

![Process duration](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_process_duration.png)

On the **Responsible** tab choose the implementation responsible, support, customer responsible and who approved the process. The **Visibility** block (Process admins only) restricts the process to selected users. Leave it empty to make the process visible to everyone.

![Process responsibles and visibility](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_process_responsible.png)

**Step 3 — Start the design**

On the process, click **Start Design**. The process moves to *Design*, the BBP start date is set (if empty), and the responsible, the customer and the step responsibles become followers.

When design is done, the status button **Start Test** (top left, in the header) moves the process to *Test*, sets the BBP end date and the completion to 100%. Do not confuse it with the **Start Test** smart button (top right, with a counter), which creates an acceptance test (Step 4).

The status buttons are available to *Process responsible* and *Process admin*. End users do not see them.

**Step 4 — Start the tests**

In the processes list, select one or more processes and open the **Actions** (gear) menu:

- **Start Internal Test**: the consultant's own test, with the implementation responsible as tester.
- **Start Integration Test**.
- **Start User Acceptance Test**: the customer's test.

![Actions menu in the processes list](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_start_tests_actions.png)

Each test is created with all the steps of the process. For several selected processes, one test is created for each. The same menu also offers **Import from library** (see Step 9) and the resets of the acceptance / internal test status on the process (existing tests are kept).

The **Start Test** smart button on the process form opens its acceptance test, creating it only if none exists yet. If there are several acceptance tests, it opens their list.

**Step 5 — Run the acceptance test**

Go to *Business process → Business process → Process Tests* and open the test. Click **Run**: the test starts, the start date is set and you become the tester if none was chosen.

For each step, the key user fills in *Data used*, *Data obtained* and the **Result** (*Passed* / *Failed*). Passed rows are green, failed rows are red, and *Test progress* shows the percentage of passed steps.

On a failed step, a smart button shows the **step issues**: it opens their list and lets you create a new issue with project, process, area and responsible already filled in.

![Acceptance test with a failed step](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_acceptance_test.png)

Click **Done** to close the test. On the process, the status of that test becomes *Done*. When no unfinished test remains, the process moves to **Done** by itself. Finishing the internal test does not change the process state, and a process already in *Done*, *Production* or *Abandoned* keeps its state.

Use **Wait** to put the test on hold (for example until test data arrives from the customer) and **Resume** to continue. **Done** marks as *Passed* only the steps still in *Draft*; failed steps stay failed. Close the test after its issues are solved.

**Step 6 — Track issues**

Go to *Business process → Business process → Issues*. An issue has a **Category** (Defect, Open issue, Improvement, Change request, Operation, Other) and a **Severity** (Critical, Major, Minor, Cosmetic). Move it through its workflow:

| Button | New state | Notes |
|---|---|---|
| **Send** | Open | marks the test step as *Failed* |
| **In progress** | Assigned | *Estimated date* becomes required |
| **Solved** | Solved | requires *Solution* and *Solution date* |
| **In test** | In customer testing | the customer rechecks |
| **Done** | Closed | requires *Closing date*; sets the test step to *Passed* if it has no other open issue |
| **Reopen** | Reopened | from *In customer testing* |
| **Set Draft** | Draft | Process admins only |

When an issue is created, the project manager receives an "Issue Submitted" email. When a development is approved, the "Development Approved" email is sent to the project manager.

![Open issue on the failed step](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_issue.png)

**Step 7 — Go live**

The process reaches **Done** either by itself when its last test is closed (Step 5), or manually with **End Testing**. The latter refuses to proceed while the process has unfinished tests and names them in the message. Open issues are not checked, so follow them in the test.

When the process is *Done*, click **Go live** to move it to *Production*. **Reset to Draft** (from any state except *Draft*) and **Abandon** are available for corrections.

**Step 8 — Reports**

Go to *Business process → Reports*:

- **Business Processes**: process steps by project, area and state. The table counts steps, not processes.

![Processes report](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_report_processes.png)

- **Business Tests**: test steps by area and result (passed / failed / draft).

![Tests report](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_report_tests.png)

- **Issues**: issues by area and severity.

![Issues report](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_report_issues.png)

From the project, **Actions → Download Excel Report** downloads `Project_Report.xlsx`: processes by area, with configuration, training, testing and migration durations and the total. Processes with a total duration of 0 are shown in red. Headers use the language of the user who downloads the report.

![Project Excel export](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_report_excel.png)

**Step 9 — Reuse processes: JSON export and import**

- **Export**: in the processes list, select the processes and choose **Actions → Export Business Process**. Pick what to include (state, tests, issues, modules, durations, developments, and on the *Contacts* tab the responsibles), then click **Export** and download the JSON file.

![Export processes to JSON](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_export_json.png)

- **Import**: on the target project form, choose **Actions → Import from file (JSON)**. Processes already in the project (same code) are updated, without durations; new ones are created. Responsibles are matched by name: a name that does not exist in the target database creates a new contact.

**Step 10 — Import from the process library**

On the project form, choose **Actions → Import from library**. The dialog asks whether to import the exported **durations** too (for all selected processes, all or nothing). Click **Continue** to list the available processes, grouped by area, with their linked modules and source.

![Process library](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_process_library.png)

Tick the processes and click **Import selected**. Each process comes with its steps and tests. The process sheet and the consultant sheets of the linked modules are attached as PDFs. A process whose code already exists in the project is skipped.

Opening the library creates any missing areas, even if you import nothing. The total project duration is updated only by **Get Duration**.
