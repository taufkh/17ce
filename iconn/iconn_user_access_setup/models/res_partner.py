# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import AccessError


class ResPartner(models.Model):
    _inherit = "res.partner"

    _ICONN_FINANCE_TAX_ALLOWED_FIELDS = {"vat"}

    iconn_company_approval_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Iconn Company Approval Status",
        copy=False,
        index=True,
        help="Approval state used by Iconn contact/company access rules.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            is_company = vals.get("is_company") or vals.get("company_type") == "company"
            if is_company and not vals.get("iconn_company_approval_state"):
                vals["iconn_company_approval_state"] = "draft"
        return super().create(vals_list)

    @api.model
    def iconn_backfill_company_approval_state(self):
        companies = self.search(
            [("is_company", "=", True), ("iconn_company_approval_state", "=", False)]
        )
        companies.write({"iconn_company_approval_state": "approved"})
        return True

    def action_iconn_company_set_draft(self):
        self.filtered("is_company").write({"iconn_company_approval_state": "draft"})
        return True

    def action_iconn_company_approve(self):
        self.filtered("is_company").write({"iconn_company_approval_state": "approved"})
        return True

    def action_iconn_company_reject(self):
        self.filtered("is_company").write({"iconn_company_approval_state": "rejected"})
        return True

    def write(self, vals):
        user = self.env.user
        if (
            vals
            and not self.env.su
            and user.has_group("iconn_user_access_setup.group_iconn_finance_officer")
            and not user.has_group("base.group_system")
        ):
            # Finance Officer is read-only for Contacts except tax-id maintenance on
            # approved company records.
            touched_fields = set(vals)
            if not touched_fields.issubset(self._ICONN_FINANCE_TAX_ALLOWED_FIELDS):
                raise AccessError(
                    "Finance role can only edit tax fields (VAT) on approved companies."
                )
            if any(not rec.is_company for rec in self):
                raise AccessError("Finance role can only edit company records for tax updates.")
            if any(rec.iconn_company_approval_state != "approved" for rec in self):
                raise AccessError(
                    "Finance role can only edit tax fields on approved companies."
                )
        return super().write(vals)
