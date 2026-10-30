# Tutorial mapping

Primary reference: [Odoo 17 Server Framework 101](https://www.odoo.com/documentation/17.0/developer/tutorials/server_framework_101.html).

| Chapters | Portfolio implementation |
| --- | --- |
| 1–3: architecture, application, models | Independent `estate` addon, manifest, property model and field defaults |
| 4–6: security, interface, views | Internal-user access rights, actions, menus, list/form/search views |
| 7: relations | Property types, tags, buyers, salespeople and offers |
| 8: compute and onchange | Total area, best offer, offer deadline with inverse, garden defaults |
| 9–10: actions and constraints | Accept/refuse, sell/cancel, SQL uniqueness and price checks, 90% selling-price rule |
| 11: interface polish | Status bar, offer decorations, editable lists, type offer count and stat action |
| 12: inheritance | Offer creation/deletion rules, inherited user model and user form |
| 13: other modules | Optional `estate_account` extension; draft invoice for 6% commission plus 100 administrative fee |
| 14: QWeb | Property Kanban view with grouping and conditional values |
| 15: final word | Installation documentation and exercises consolidated in a portfolio |

## Learning attribution

The repository owner's learning sources include Muhammad Nasser's Arabic Odoo 17 Development Course and the official Odoo documentation. This is an independent tutorial implementation; it is not an official Odoo application or an endorsed course solution. No course videos, paid materials, or instructor source archives are included.

Odoo's upstream source is obtained separately from [odoo/odoo, branch 17.0](https://github.com/odoo/odoo/tree/17.0). It is not vendored into this repository. The tutorial's exercise specifications guide the addon behavior; the repository includes its own tests and setup documentation.
