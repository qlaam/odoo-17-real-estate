from odoo import Command, _, fields, models
from odoo.exceptions import UserError


class EstateProperty(models.Model):
    _inherit = "estate.property"

    invoice_id = fields.Many2one(
        "account.move",
        string="Sale Invoice",
        readonly=True,
        copy=False,
        check_company=True,
        ondelete="restrict",
        help="The original sale invoice, retained even if it is cancelled.",
    )

    def action_sold(self):
        if not self:
            return super().action_sold()
        self.check_access_rights("write")
        self.check_access_rule("write")
        with self.env.cr.savepoint():
            self.flush_recordset()
            self.env.cr.execute(
                "SELECT id FROM estate_property WHERE id IN %s "
                "ORDER BY id FOR UPDATE",
                [tuple(self.ids)],
            )
            self.invalidate_recordset()
            for property_record in self:
                if property_record.invoice_id or property_record.state == "sold":
                    raise UserError(_("This property has already been sold or invoiced."))
                if not property_record.buyer_id:
                    raise UserError(_("Select a buyer before selling a property."))
                if property_record.selling_price <= 0:
                    raise UserError(_("The selling price must be greater than zero."))
                if not property_record.company_id:
                    raise UserError(_("Select a company before selling a property."))

            result = super().action_sold()
            for property_record in self:
                invoice = self.env["account.move"].with_company(
                    property_record.company_id
                ).create({
                    "move_type": "out_invoice",
                    "partner_id": property_record.buyer_id.id,
                    "company_id": property_record.company_id.id,
                    "currency_id": property_record.company_id.currency_id.id,
                    "invoice_origin": property_record.display_name,
                    "invoice_line_ids": [
                        Command.create({
                            "name": _("Commission (6%%): %s", property_record.display_name),
                            "quantity": 1.0,
                            "price_unit": property_record.selling_price * 0.06,
                            "tax_ids": [Command.clear()],
                        }),
                        Command.create({
                            "name": _("Administrative fees"),
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "tax_ids": [Command.clear()],
                        }),
                    ],
                })
                property_record.invoice_id = invoice
            return result
