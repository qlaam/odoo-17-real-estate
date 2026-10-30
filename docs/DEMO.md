# Portfolio walkthrough

This learning project implements Odoo 17's official Server Framework 101 real estate application. The README contains setup and attribution details.

## Five-minute demonstration

1. Install **Real Estate** and open **Real Estate → Properties**. Create a property with an expected price of 100,000, a property type, living area and garden. Changing the garden checkbox demonstrates an onchange; the total area demonstrates a computed field.
2. Add tags and a buyer contact. Create an offer for 95,000. Check its validity period and calculated deadline. Try a lower subsequent offer to demonstrate the offer creation rule.
3. Accept the offer. The property records the buyer and selling price. Attempting to accept another offer demonstrates the single accepted offer rule.
4. Mark the property sold. A sold property cannot be canceled. Open the property type to inspect its offer count and related offers.
5. Switch to Kanban and inspect the property grouping. Search and group properties with the search view. An administrator can inspect a salesperson's available properties on the user form.
6. With **Real Estate Accounting** installed and a sales journal/chart of accounts configured, repeat a sale for a new property. Open Invoicing and inspect the draft customer invoice: a 95,000 sale produces a 5,700 commission line and a 100 administrative fee line, before any configured taxes.

Use fictional contacts and properties for demonstrations. Invoice amounts represent the tutorial's illustrative commission model.

## Suggested CV wording

> Implemented an Odoo 17 real estate application following the official Server Framework 101 tutorial, with relational models, computed fields, business constraints, XML views, access controls, and a separate accounting integration generating customer invoices.

Mention automated runtime test results only after running the documented commands successfully in your environment. Screenshots should come from your running installation.
