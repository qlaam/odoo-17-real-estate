from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Property Offer"
    _order = "price desc, id desc"

    price = fields.Float(required=True)
    status = fields.Selection([
        ("accepted", "Accepted"), ("refused", "Refused"),
    ], copy=False, readonly=True)
    partner_id = fields.Many2one("res.partner", string="Buyer", required=True)
    property_id = fields.Many2one("estate.property", required=True, ondelete="cascade")
    property_type_id = fields.Many2one(related="property_id.property_type_id", store=True)
    validity = fields.Integer(default=7, required=True, string="Validity (days)")
    date_deadline = fields.Date(compute="_compute_date_deadline", inverse="_inverse_date_deadline", store=True)

    _sql_constraints = [
        ("price_positive", "CHECK(price > 0)", "The offer price must be strictly positive."),
        ("validity_nonnegative", "CHECK(validity >= 0)", "Validity cannot be negative."),
    ]

    def _base_date(self):
        self.ensure_one()
        return fields.Date.to_date(self.create_date) if self.create_date else fields.Date.context_today(self)

    @api.depends("create_date", "validity")
    def _compute_date_deadline(self):
        for offer in self:
            offer.date_deadline = offer._base_date() + timedelta(days=offer.validity)

    def _inverse_date_deadline(self):
        for offer in self:
            if offer.date_deadline:
                offer.validity = (offer.date_deadline - offer._base_date()).days

    @api.model_create_multi
    def create(self, vals_list):
        offers = self.browse()
        for vals in vals_list:
            property_id = vals.get("property_id") or self.env.context.get("default_property_id")
            property_record = self.env["estate.property"].browse(property_id).exists()
            if property_record:
                if property_record.state not in ("new", "offer_received"):
                    raise UserError(_("Offers can only be added to available properties."))
                if float_compare(vals.get("price", 0), property_record.best_price, precision_digits=2) < 0:
                    raise ValidationError(_("An offer cannot be lower than an existing offer."))
            if vals.get("status"):
                raise UserError(_("Use the Accept or Refuse actions to decide an offer."))
            offer = super().create([vals])
            offer.property_id.write({"state": "offer_received"})
            offers |= offer
        return offers

    def write(self, vals):
        if any(offer.status == "accepted" for offer in self) and set(vals) & {"price", "partner_id", "property_id"}:
            raise UserError(_("An accepted offer's price, buyer and property cannot be changed."))
        if "property_id" in vals and any(offer.property_id.id != vals["property_id"] for offer in self):
            raise UserError(_("Create a new offer instead of moving an existing offer."))
        if "price" in vals:
            for offer in self:
                if offer.property_id.state not in ("new", "offer_received"):
                    raise UserError(_("Offers on unavailable properties cannot be changed."))
                other_prices = (offer.property_id.offer_ids - offer).mapped("price")
                if float_compare(vals["price"], max(other_prices, default=0), precision_digits=2) < 0:
                    raise ValidationError(_("An offer cannot be lower than an existing offer."))
        return super().write(vals)

    @api.constrains("status", "property_id")
    def _check_one_accepted_offer(self):
        for offer in self:
            if offer.status == "accepted" and len(offer.property_id.offer_ids.filtered(lambda item: item.status == "accepted")) > 1:
                raise ValidationError(_("Only one offer can be accepted for a property."))

    @api.ondelete(at_uninstall=False)
    def _unlink_except_accepted(self):
        if any(offer.status == "accepted" for offer in self):
            raise UserError(_("An accepted offer cannot be deleted."))

    def action_accept(self):
        self.ensure_one()
        if self.status:
            raise UserError(_("Only a pending offer can be accepted."))
        if self.property_id.state not in ("new", "offer_received"):
            raise UserError(_("This property is no longer available."))
        if self.property_id.offer_ids.filtered(lambda offer: offer.status == "accepted"):
            raise UserError(_("An offer has already been accepted for this property."))
        self.property_id.write({
            "buyer_id": self.partner_id.id,
            "selling_price": self.price,
            "state": "offer_accepted",
        })
        self.status = "accepted"
        return True

    def action_refuse(self):
        if any(offer.status for offer in self):
            raise UserError(_("Only pending offers can be refused."))
        if any(offer.property_id.state in ("sold", "canceled") for offer in self):
            raise UserError(_("Offers on sold or canceled properties cannot be refused."))
        self.write({"status": "refused"})
        return True
