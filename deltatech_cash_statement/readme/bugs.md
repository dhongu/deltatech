# Bug review — Cash Statement

Review date: 2026-10-02. Target version: Odoo 19.

## CASHBALANCE-001 — P1: Balance update chains statements from different journals

- **Status:** Open.
- **Location:** wizard/account_cash_update_balances.py, default_get() and do_update_balance().
- **Trigger:** Select bank/cash statements belonging to different journals and run Cash Update Balances.
- **Actual behavior:** Both searches accept all selected IDs without checking journal/company/currency consistency. do_update_balance orders them by date and carries each statement's ending balance into the next statement's starting balance, even across unrelated journals. It also overwrites each real ending balance with the computed ending balance.
- **Evidence:** Executed actual extracted update method on mock statements in journals 1 and 2 with starting input 100 and movements +50/+20: journal 2 received starting balance 150 from journal 1. The list-bound action has no selection restriction and the method contains no journal validation.
- **Impact:** A mixed selection overwrites independent journal cash balances, potentially copying nominal amounts across different currencies or allowed companies.
- **Suggested fix:** Require one journal/company/currency per operation or process independent journal chains with explicitly defined starting balances. Do not erase real closing balance discrepancies without deliberate user intent.
- **Validation needed:** Mixed journals rejected/preserved, single-journal chronological sequence, differing currencies/companies and actual ending balance discrepancy.

## Review limitations

All eligible source and ACL read. Actual update method exercised with mock statements only; no Odoo accounting/database writes or integration tests executed.
