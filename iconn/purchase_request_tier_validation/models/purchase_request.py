# Copyright 2019-2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models
from odoo.exceptions import ValidationError


class PurchaseRequest(models.Model):
    _name = "purchase.request"
    _inherit = ["purchase.request", "tier.validation"]
    _state_from = ["draft"]
    _state_to = ["approved"]

    _tier_validation_manual_config = False

    @api.model
    def _get_under_validation_exceptions(self):
        res = super(PurchaseRequest, self)._get_under_validation_exceptions()
        res.append("route_id")
        return res

    def button_approved(self):
        for rec in self:
            if rec.need_validation:
                raise ValidationError('Approval required to confirm this Purchase Request.')
        res = super(PurchaseRequest, self).button_approved()
        return res
