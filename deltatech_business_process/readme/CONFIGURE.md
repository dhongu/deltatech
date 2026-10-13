## Access rights

Go to *Settings → Users* and, for each user, set the **Business process** access level:

- **Process admin**: creates projects and processes, configures areas and the library.
- **Process responsible**: writes steps, developments and tests, and moves processes through their lifecycle.
- **End user**: runs acceptance tests, records results on steps and opens issues.

The groups are inherited: Process admin includes Process responsible, which includes End user.

## Master data

Go to *Business process → Configuration*:

- **Area**: create the areas of the project (Sales, Purchasing, Inventory, Accounting…). An area can have *Process groups* and a **Responsible**, who is automatically set as *Implementation responsible* on new processes in that area.
- **Implementation Stage**: three stages exist after installation. Rename them to match your project plan.
- **Development Type**, **Business Role**, **Transactions**: optional lists, in the same menu.

## Process library (optional)

Go to *Business process → Configuration → Process Library*:

- **Discover processes from all modules** (on by default): any installed module with a `processes/` folder becomes a source.
- **Limit to modules**: comma-separated list; when filled in, only these modules are sources.
- **Git repositories**: comma-separated URLs, then **Sync now**.
- **Private repository credentials**: user name and token for private HTTPS repositories.

![Process library settings](https://apps.odoocdn.com/apps/assets/19.0/deltatech_business_process/bp_library_settings.png)
