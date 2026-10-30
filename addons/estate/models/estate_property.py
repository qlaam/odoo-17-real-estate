from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Real Estate Property"
    _order = "id desc"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(
        string="Available From", copy=False,
        default=lambda self: fields.Date.context_today(self) + relativedelta(months=3),
    )
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer(string="Living Area (sqm)")
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer(string="Garden Area (sqm)")
    garden_orientation = fields.Selection([
        ("north", "North"), ("south", "South"),
        ("east", "East"), ("west", "West"),
    ])
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ("new", "New"), ("offer_received", "Offer Received"),
        ("offer_accepted", "Offer Accepted"), ("sold", "Sold"),
        ("canceled", "Canceled"),
    ], required=True, default="new", copy=False)
    property_type_id = fields.Many2one("estate.property.type", string="Property Type")
    buyer_id = fields.Many2one("res.partner", string="Buyer", copy=False, readonly=True)
    salesperson_id = fields.Many2one(
        "res.users", string="Salesperson", default=lambda self: self.env.user,
    )
    tag_ids = fields.Many2many("estate.property.tag", string="Tags")
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    total_area = fields.Integer(compute="_compute_total_area", string="Total Area (sqm)")
    best_price = fields.Float(compute="_compute_best_price", string="Best Offer")

    _sql_constraints = [
        ("expected_price_positive", "CHECK(expected_price > 0)", "Expected price must be strictly positive."),
        ("selling_price_nonnegative", "CHECK(selling_price >= 0)", "Selling price cannot be negative."),
        ("areas_nonnegative", "CHECK(living_area >= 0 AND garden_area >= 0)", "Areas cannot be negative."),
        ("rooms_nonnegative", "CHECK(bedrooms >= 0 AND facades >= 0)", "Bedrooms and facades cannot be negative."),
    ]

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        for record in self:
            record.best_price = max(record.offer_ids.mapped("price"), default=0.0)

    @api.onchange("garden")
    def _onchange_garden(self):
        for record in self:
            record.garden_area = 10 if record.garden else 0
            record.garden_orientation = "north" if record.garden else False

    @api.constrains("expected_price", "selling_price")
    def _check_selling_price(self):
        for record in self:
            if not float_is_zero(record.selling_price, precision_digits=2) and float_compare(
                record.selling_price, 0.9 * record.expected_price, precision_digits=2,
            ) < 0:
                raise ValidationError(_("The selling price must be at least 90% of the expected price."))

    @api.ondelete(at_uninstall=False)
    def _unlink_except_new_or_canceled(self):
        if any(record.state not in ("new", "canceled") for record in self):
            raise UserError(_("Only new or canceled properties can be deleted."))

    def action_sold(self):
        if any(record.state == "canceled" for record in self):
            raise UserError(_("A canceled property cannot be sold."))
        if any(record.state == "sold" for record in self):
            raise UserError(_("This property has already been sold."))
        if any(record.state != "offer_accepted" or not record.buyer_id or not record.selling_price for record in self):
            raise UserError(_("Accept an offer before selling a property."))
        self.write({"state": "sold"})
        return True

    def action_cancel(self):
        if any(record.state == "sold" for record in self):
            raise UserError(_("A sold property cannot be canceled."))
        self.write({"state": "canceled"})
        return True
