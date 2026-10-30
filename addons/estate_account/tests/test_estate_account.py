from unittest.mock import patch

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestEstateAccount(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Property = cls.env["estate.property"]

    def _property(self, **values):
        return self.Property.create({
            "name": "Accounting test property",
            "state": "offer_accepted",
            "expected_price": 100000.0,
            "selling_price": 100000.0,
            "buyer_id": self.partner_a.id,
            "company_id": self.company_data["company"].id,
            **values,
        })

    def test_sale_creates_draft_invoice(self):
        property_record = self._property()
        property_record.action_sold()
        invoice = property_record.invoice_id
        self.assertTrue(invoice)
        self.assertEqual(property_record.state, "sold")
        self.assertEqual(invoice.state, "draft")
        self.assertEqual(invoice.move_type, "out_invoice")
        self.assertEqual(invoice.partner_id, self.partner_a)
        self.assertEqual(invoice.company_id, property_record.company_id)
        self.assertEqual(invoice.currency_id, property_record.company_id.currency_id)
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        self.assertEqual(sorted(invoice.invoice_line_ids.mapped("price_unit")), [100.0, 6000.0])
        self.assertEqual(invoice.invoice_line_ids.mapped("quantity"), [1.0, 1.0])
        self.assertAlmostEqual(invoice.amount_total, 6100.0)

    def test_repeated_sale_does_not_duplicate_invoice(self):
        property_record = self._property()
        property_record.action_sold()
        invoice = property_record.invoice_id
        count = self.env["account.move"].search_count([])
        with self.assertRaises(UserError):
            property_record.action_sold()
        self.assertEqual(property_record.invoice_id, invoice)
        self.assertEqual(self.env["account.move"].search_count([]), count)

    def test_cancelled_invoice_does_not_allow_another_sale(self):
        property_record = self._property()
        property_record.action_sold()
        property_record.invoice_id.button_cancel()
        with self.assertRaises(UserError):
            property_record.action_sold()

    def test_missing_buyer(self):
        property_record = self._property(buyer_id=False)
        with self.assertRaises(UserError):
            property_record.action_sold()
        self.assertFalse(property_record.invoice_id)
        self.assertNotEqual(property_record.state, "sold")

    def test_zero_selling_price(self):
        property_record = self._property(selling_price=0)
        with self.assertRaises(UserError):
            property_record.action_sold()
        self.assertFalse(property_record.invoice_id)

    def test_cancelled_property_is_not_invoiced(self):
        property_record = self._property(state="canceled")
        with self.assertRaises(UserError):
            property_record.action_sold()
        self.assertFalse(property_record.invoice_id)

    def test_batch_sale(self):
        properties = self._property() | self._property(selling_price=200000.0)
        properties.action_sold()
        self.assertEqual(len(properties.mapped("invoice_id")), 2)
        self.assertEqual(set(properties.mapped("state")), {"sold"})
        self.assertEqual(sorted(properties.mapped("invoice_id.amount_total")), [6100.0, 12100.0])

    def test_batch_validation_does_not_partially_sell(self):
        valid = self._property()
        invalid = self._property(buyer_id=False)
        with self.assertRaises(UserError):
            (valid | invalid).action_sold()
        self.assertNotEqual(valid.state, "sold")
        self.assertFalse(valid.invoice_id)

    def test_invoice_failure_rolls_back_sale(self):
        property_record = self._property()
        original_state = property_record.state
        with patch.object(type(self.env["account.move"]), "create", side_effect=UserError("Invoice failed")):
            with self.assertRaises(UserError):
                property_record.action_sold()
        self.assertEqual(property_record.state, original_state)
        self.assertFalse(property_record.invoice_id)

    def test_property_company_overrides_active_company(self):
        company = self.company_data_2["company"]
        self.env.user.write({"company_ids": [Command.link(company.id)]})
        property_record = self._property(company_id=company.id)
        property_record.action_sold()
        self.assertEqual(property_record.invoice_id.company_id, company)
        self.assertEqual(property_record.invoice_id.journal_id.company_id, company)
        self.assertEqual(property_record.invoice_id.currency_id, company.currency_id)

    def test_copy_does_not_copy_invoice_link(self):
        property_record = self._property()
        property_record.action_sold()
        self.assertFalse(property_record.copy().invoice_id)
