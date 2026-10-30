# Odoo 17 Real Estate Portfolio

[![Odoo 17 integration](https://github.com/qlaam/odoo-17-real-estate/actions/workflows/ci.yml/badge.svg)](https://github.com/qlaam/odoo-17-real-estate/actions/workflows/ci.yml)

A learning portfolio for Odoo 17 Community, organized into `estate` (real estate management) and `estate_account` (accounting integration). This is an educational project; runtime verification is still required.

## Learning attribution

The portfolio author learned from **Muhammad Nasser's Arabic Odoo 17 Development Course** and the official [Odoo 17 Server Framework 101 tutorial](https://www.odoo.com/documentation/17.0/developer/tutorials/server_framework_101.html). This portfolio applies those learning topics. It is independently maintained and does not claim endorsement, certification, or affiliation with Muhammad Nasser or Odoo. The course materials and Odoo trademarks remain the property of their respective owners.

## Tutorial coverage

See the [tutorial notes](docs/TUTORIAL.md) and [demo walkthrough](docs/DEMO.md) for the accompanying learning and demonstration guides.

The intended tutorial scope is summarized below. Check the addon source and test results to establish what currently works; this table is not a claim that every exercise is complete.

| Area | Portfolio scope |
| --- | --- |
| Application structure | Addon manifests, Python imports, menus and actions |
| Models and fields | Properties, property types, tags and offers; basic and relational fields |
| Computed values | Total area, best offer and offer validity dates |
| User interface | List, form and search views, filters, grouping and inline relations |
| Business logic | Offer acceptance/refusal, sale/cancellation and constraints |
| Inheritance | ORM overrides and extension of existing models/views |
| Accounting | Separate `estate_account` bridge depending on `estate` and `account` |
| Security and testing | Internal-user access rights and Odoo integration tests |

## Layout

```text
addons/estate/          Real estate addon (maintained separately)
addons/estate_account/  Accounting bridge (maintained separately)
scripts/verify.py      Dependency-free AST, XML and manifest checks
compose.yaml           Odoo 17 and PostgreSQL 15 development services
.github/workflows/ci.yml
```

## Run with Docker Compose

Requires Docker with Compose v2 and Python 3.10+ for the static checker. Run commands from this portfolio directory. The images and configuration follow the [official Odoo image documentation](https://hub.docker.com/_/odoo).

```sh
python scripts/verify.py
docker compose up -d db
docker compose run --rm odoo odoo -d estate_dev -i estate,estate_account --stop-after-init --without-demo=all
docker compose up -d odoo
```

Open [Odoo locally](http://localhost:8069), select `estate_dev`, and use the initial local database administrator credentials `admin` / `admin`; change them after login. This setup uses development credentials, binds the web port to localhost, and is not a production deployment. PostgreSQL and Odoo data persist in named volumes.

```sh
docker compose logs -f odoo
docker compose down
```

`down` keeps the named volumes. Do not remove volumes unless you intend to delete the development databases and filestore.

## Integration tests

Use a fresh database name for each test run (replace `estate_test_001` if it already exists):

```sh
docker compose up -d db
docker compose run --rm odoo odoo -d estate_test_001 -i estate,estate_account --test-enable --test-tags /estate,/estate_account --stop-after-init --without-demo=all
```

The essential test command is `odoo -i estate,estate_account --test-enable --test-tags /estate,/estate_account --stop-after-init --without-demo=all`; Compose supplies database connectivity and the extra addon mount. The tags select the portfolio tests, excluding unrelated upstream test suites. Inspect the final Odoo test summary and failures, not just container startup. CI runs the static checker and this integration command against a fresh Compose project, checks that an Odoo test summary exists and reports tests, and uploads logs even on failure.

**Verification status:** no passing integration-test result is claimed here. The static checker checks syntax and manifest structure only; it does not install Odoo, validate view semantics, exercise access rules, or prove business behavior. No screenshots are included and no visual verification is claimed.

## Optional Odoo source checkout

Keep upstream Odoo outside the portfolio. From the workspace root (the directory containing `outputs`), use:

```sh
mkdir -p work
git clone --depth 1 --branch 17.0 https://github.com/odoo/odoo.git work/odoo
```

On PowerShell, create the directory with `New-Item -ItemType Directory -Force work` instead of `mkdir -p`. If `work/odoo` already exists, use that checkout rather than cloning over it. The resulting paths are siblings through the workspace root: `work/odoo` and `outputs/odoo17-estate-portfolio`. Do not copy Odoo's source or its `.git` directory into this portfolio.

For a source-based run, follow the official [Odoo 17 source installation instructions](https://www.odoo.com/documentation/17.0/administration/on_premise/source.html) for system dependencies, PostgreSQL and a Python environment. From the workspace root, after configuring database credentials:

```sh
python work/odoo/odoo-bin --addons-path=work/odoo/addons,outputs/odoo17-estate-portfolio/addons -d estate_test_source -i estate,estate_account --test-enable --test-tags /estate,/estate_account --stop-after-init --without-demo=all
```

Docker Compose does not require a source checkout. The `17.0` branch and image tags can change over time; record the source commit and image digests when publishing reproducible test evidence.

## License

Portfolio code is licensed under GNU LGPL version 3 (`LGPL-3.0-only`); see [LICENSE](LICENSE). This does not relicense upstream Odoo, course materials, or other third-party content. GNU GPL version 3, whose provisions are incorporated by LGPL v3, is available at [GNU](https://www.gnu.org/licenses/gpl-3.0.html).
