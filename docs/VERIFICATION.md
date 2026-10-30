# Verification evidence

Verified on 30 October 2026.

## Native core installation

- Official Odoo 17 source commit: `220f33cd7fda4a40af8372c33905d953d0b267dc`, branch `17.0`.
- Windows, Python 3.10, PostgreSQL 15 on an isolated local test cluster.
- Fresh `estate` installation completed. After correcting test expectations, an update/test run returned exit code 0: **21 tests, zero failures, zero errors**.
- Database inspection confirmed `estate` installed with `account` and `estate_account` uninstalled.
- The source checkout is shallow, filtered and sparse. Upstream behavior was not modified. The Python environment inherited existing packages; this native run is not a claim of a clean, fully pinned dependency installation.

## Combined accounting verification

- [GitHub Actions run 41077253111](https://github.com/qlaam/odoo-17-real-estate/actions/runs/41077253111) completed successfully for addon code commit `c1395ece00433c396b29d52dc81dd8d288fc539a`.
- The CI workflow installs both addons into a fresh PostgreSQL 15 database using the official `odoo:17.0` container, then runs `/estate,/estate_account` tests. All **32 tests passed with zero failures and zero errors**.
- Native Windows verification also installed `estate`, `account` and `estate_account`. The final update/test run on that database passed **32 tests with zero failures and zero errors**, exit code 0.
- These are 21 core tests and 11 accounting tests. They cover model behavior, onchange forms, SQL/Python constraints, access rights, inherited views, report HTML, draft invoice amounts, company selection, duplicate sale protection and rollback on invoice failure.
- Early runs exposed test expectation errors; those were corrected before the passing runs. Historical failed runs remain visible in Actions.

## Static validation

`python scripts/verify.py` passes Python AST parsing, XML parsing and manifest file/dependency checks. `git diff --check` passes. These checks complement runtime tests; they do not prove browser behavior.

## Limitations

No browser walkthrough, screenshot capture or PDF rendering has been verified. The report's HTML rendering is covered by an Odoo test. No production deployment or production accounting configuration is claimed.
