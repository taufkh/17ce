# Copyright 2017 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "tier.validation"]
    _state_from = ["draft", "sent", "to approve"]
    _state_to = ["purchase", "approved"]

    _tier_validation_manual_config = False

    def button_confirm(self):
        for rec in self:
            if rec.need_validation:
                raise ValidationError('Approval required to confirm this Purchase Order.')
        res = super(PurchaseOrder, self).button_confirm()
        return res
