from datetime import timedelta

from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, TransactionCase, tagged
from odoo.tools import mute_logger

from ..models.estate_property import EstateProperty


@tagged("post_install", "-at_install")
class TestEstate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Property = cls.env["estate.property"]
        cls.Offer = cls.env["estate.property.offer"]
        cls.property_type = cls.env["estate.property.type"].create({"name": "Test House"})
        cls.buyer, cls.other_buyer = cls.env["res.partner"].create([
            {"name": "Estate Buyer"}, {"name": "Other Estate Buyer"},
        ])
        cls.property = cls.Property.create({
            "name": "Test Property", "expected_price": 100000,
            "property_type_id": cls.property_type.id,
            "living_area": 80, "garden_area": 20,
        })

    def _offer(self, price=95000, property_record=None, partner=None):
        return self.Offer.create({
            "price": price,
            "partner_id": (partner or self.buyer).id,
            "property_id": (property_record or self.property).id,
        })

    def test_defaults_and_computed_area(self):
        self.assertEqual(self.property.state, "new")
        self.assertEqual(self.property.bedrooms, 2)
        self.assertTrue(self.property.active)
        self.assertEqual(self.property.salesperson_id, self.env.user)
        self.assertEqual(self.property.company_id, self.env.company)
        self.assertEqual(self.property.date_availability, fields.Date.context_today(self.property) + relativedelta(months=3))
        self.assertEqual(self.property.total_area, 100)
        self.assertEqual(self.property.best_price, 0)
        self.property.living_area = 90
        self.assertEqual(self.property.total_area, 110)

    def test_garden_onchange(self):
        with Form(self.Property) as property_form:
            property_form.name = "Garden Form"
            property_form.expected_price = 100000
            property_form.garden = True
            self.assertEqual(property_form.garden_area, 10)
            self.assertEqual(property_form.garden_orientation, "north")
            property_form.garden = False
        self.assertEqual(property_form.record.garden_area, 0)
        self.assertFalse(property_form.record.garden_orientation)

    def test_offer_creation_and_best_price(self):
        first = self._offer(90000)
        second = self._offer(95000, partner=self.other_buyer)
        self.assertEqual(self.property.state, "offer_received")
        self.assertEqual(self.property.best_price, 95000)
        second.action_refuse()
        self.assertEqual(second.status, "refused")
        self.assertEqual(self.property.best_price, 95000)
        self.assertFalse(first.status)

    def test_lower_offer_rejected_and_equal_allowed(self):
        self._offer()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self._offer(94000)
        self._offer(95000, partner=self.other_buyer)
        self.assertEqual(len(self.property.offer_ids), 2)

    def test_batch_offers_respect_existing_and_batch_prices(self):
        values = {
            "partner_id": self.buyer.id,
            "property_id": self.property.id,
        }
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.Offer.create([dict(values, price=95000), dict(values, price=90000)])
        self.assertFalse(self.property.offer_ids)
        self.assertEqual(self.property.state, "new")
        offers = self.Offer.create([dict(values, price=90000), dict(values, price=95000)])
        self.assertEqual(len(offers), 2)
        self.assertEqual(self.property.best_price, 95000)

    def test_deadline_compute_inverse_and_unsaved_fallback(self):
        offer = self._offer()
        base_date = fields.Date.to_date(offer.create_date)
        self.assertEqual(offer.validity, 7)
        self.assertEqual(offer.date_deadline, base_date + timedelta(days=7))
        offer.validity = 14
        self.assertEqual(offer.date_deadline, base_date + timedelta(days=14))
        offer.date_deadline = base_date + timedelta(days=21)
        self.assertEqual(offer.validity, 21)
        draft = self.Offer.new({"validity": 7})
        self.assertEqual(draft.date_deadline, fields.Date.context_today(draft) + timedelta(days=7))

    def test_accept_and_sell(self):
        offer = self._offer()
        self.assertTrue(offer.action_accept())
        self.assertEqual(offer.status, "accepted")
        self.assertEqual(self.property.buyer_id, self.buyer)
        self.assertEqual(self.property.selling_price, offer.price)
        self.assertEqual(self.property.state, "offer_accepted")
        self.assertTrue(EstateProperty.action_sold(self.property))
        self.assertEqual(self.property.state, "sold")
        with self.assertRaises(UserError):
            self.property.action_cancel()
        with self.assertRaises(UserError):
            EstateProperty.action_sold(self.property)

    def test_only_one_offer_accepted(self):
        first = self._offer(90000)
        second = self._offer(95000, partner=self.other_buyer)
        first.action_accept()
        with self.assertRaises(UserError):
            second.action_accept()
        with self.assertRaises(UserError):
            first.action_refuse()
        with self.assertRaises(UserError):
            first.write({"price": 98000})
        with self.assertRaises(UserError):
            first.unlink()

    def test_refused_offer_cannot_be_accepted(self):
        offer = self._offer()
        offer.action_refuse()
        with self.assertRaises(UserError):
            offer.action_accept()

    def test_cancellation_and_unavailable_offers(self):
        self.property.action_cancel()
        with self.assertRaises(UserError):
            EstateProperty.action_sold(self.property)
        with self.assertRaises(UserError):
            self._offer()
        other = self.Property.create({"name": "Accepted", "expected_price": 100000})
        self._offer(property_record=other).action_accept()
        with self.assertRaises(UserError):
            self._offer(100000, property_record=other)

    def test_sale_requires_accepted_offer(self):
        with self.assertRaises(UserError):
            EstateProperty.action_sold(self.property)

    def test_selling_price_threshold(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.property.selling_price = 89999
        self.property.selling_price = 90000
        self.property.selling_price = 0
        offer = self._offer(89999)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            offer.action_accept()
        self.assertFalse(offer.status)
        self.assertFalse(self.property.buyer_id)

    def test_threshold_rechecked_when_expected_price_changes(self):
        self.property.selling_price = 90000
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.property.expected_price = 110000

    def test_sql_constraints(self):
        invalid_properties = [
            {"expected_price": 0}, {"expected_price": -1},
            {"selling_price": -1}, {"living_area": -1},
            {"garden_area": -1}, {"bedrooms": -1}, {"facades": -1},
        ]
        for values in invalid_properties:
            with self.subTest(values=values), mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError), self.cr.savepoint():
                self.Property.create(dict({"name": "Invalid", "expected_price": 100000}, **values))
        for values in ({"price": 0}, {"price": -1}, {"price": 95000, "validity": -1}):
            with self.subTest(values=values), mute_logger("odoo.sql_db"), self.assertRaises((IntegrityError, ValidationError)), self.cr.savepoint():
                self.Offer.create(dict({"partner_id": self.buyer.id, "property_id": self.property.id}, **values))

    def test_unique_type_and_tag_names(self):
        self.env["estate.property.tag"].create({"name": "Unique Tag"})
        for model, name in (("estate.property.type", "Test House"), ("estate.property.tag", "Unique Tag")):
            with self.subTest(model=model), mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError), self.cr.savepoint():
                self.env[model].create({"name": name})

    def test_unlink_guard_for_recordsets(self):
        new_property = self.Property.create({"name": "New", "expected_price": 100000})
        self._offer()
        with self.assertRaises(UserError):
            (new_property | self.property).unlink()
        self.assertTrue(new_property.exists())
        self.property.action_cancel()
        (new_property | self.property).unlink()
        self.assertFalse(self.property.exists())

    def test_copy_does_not_retain_sale_details(self):
        self._offer().action_accept()
        duplicate = self.property.copy()
        self.assertEqual(duplicate.state, "new")
        self.assertFalse(duplicate.buyer_id)
        self.assertEqual(duplicate.selling_price, 0)
        self.assertFalse(duplicate.offer_ids)
        self.assertEqual(duplicate.salesperson_id, self.property.salesperson_id)

    def test_type_related_offers_and_action(self):
        offer = self._offer()
        self.assertEqual(offer.property_type_id, self.property_type)
        self.assertEqual(self.property_type.offer_count, 1)
        self.assertEqual(self.property_type.offer_ids, offer)
        action = self.property_type.action_view_offers()
        self.assertEqual(action["res_model"], "estate.property.offer")
        self.assertEqual(action["domain"], [("property_type_id", "=", self.property_type.id)])

    def test_user_available_properties(self):
        user = self.property.salesperson_id
        self.assertIn(self.property, user.property_ids)
        self._offer()
        user.invalidate_recordset(["property_ids"])
        self.assertIn(self.property, user.property_ids)
        self.property.offer_ids.action_accept()
        user.invalidate_recordset(["property_ids"])
        self.assertNotIn(self.property, user.property_ids)

    def test_internal_user_access_and_portal_denied(self):
        internal = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Estate Internal", "login": "estate_test_internal",
            "groups_id": [Command.set([self.env.ref("base.group_user").id])],
        })
        portal = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Estate Portal", "login": "estate_test_portal",
            "groups_id": [Command.set([self.env.ref("base.group_portal").id])],
        })
        property_record = self.Property.with_user(internal).create({"name": "Internal", "expected_price": 100000})
        self.assertEqual(property_record.salesperson_id, internal)
        property_record.write({"postcode": "12345"})
        property_record.unlink()
        for model in ("estate.property", "estate.property.offer", "estate.property.type", "estate.property.tag"):
            with self.subTest(model=model), self.assertRaises(AccessError):
                self.env[model].with_user(portal).check_access_rights("read")

    def test_report_html_and_user_view(self):
        self._offer()
        html, report_type = self.env["ir.actions.report"]._render_qweb_html(
            "estate.action_report_estate_property", self.property.ids,
        )
        self.assertEqual(report_type, "html")
        self.assertIn(b"Test Property", html)
        self.assertIn(b"Estate Buyer", html)
        user_view = self.env["res.users"].get_view(self.env.ref("base.view_users_form").id, "form")
        self.assertIn("estate_properties", user_view["arch"])
        self.assertIn("property_ids", user_view["arch"])
