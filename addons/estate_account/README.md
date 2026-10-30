# Estate Accounting (Odoo 17)

Optional bridge depending on `estate` and `account`. Extends
`estate.property.action_sold()` and preserves its return value. Each sale creates
one draft customer invoice for the buyer in the property's company and currency,
with two untaxed lines: 6% of selling price and a 100 administrative fee.
Configure the company's sales journal and chart of accounts before use. Users
need normal permissions to sell properties and create customer invoices; no
permissions are elevated by this addon.

Accounting users can open the linked invoice from the property's Invoicing
section. The extension inherits the core form `estate.estate_property_view_form`.

The readonly, noncopied `invoice_id` retains the original invoice, including when
cancelled, and prevents its deletion while linked. A repeated sale raises
`UserError`. Property row locks serialize concurrent sale attempts; Odoo's
transaction retry handles serialization conflicts. A savepoint rolls back the
entire batch if a sale or invoice fails. Existing sold properties are rejected
without creating retrospective invoices.

Source: [Odoo 17 Chapter 13: Interact With Other Modules](https://www.odoo.com/documentation/17.0/developer/tutorials/server_framework_101/13_other_module.html).

Run integration tests against a disposable Odoo 17 database with both addons on
the addons path:

```sh
odoo-bin -d estate_test --addons-path=odoo/addons,addons -i estate_account --test-enable --test-tags /estate_account --stop-after-init
```

Tests cover draft amounts and buyer, repeated and cancelled invoice sales,
invalid sales, batches, rollback on accounting failure, company selection, and
copy behavior. The core addon must expose `state` (`sold` / `canceled`),
`expected_price`, `buyer_id`, `selling_price`, `company_id`, and `action_sold`.
