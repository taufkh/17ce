# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountAccountTypeCompat(models.Model):
    _name = "account.account.type"
    _description = "Account Type (Compatibility)"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ("account_type_compat_code_unique", "unique(code)", "Code must be unique."),
    ]

    @api.model
    def _sync_from_account_type_selection(self):
        account_type_field = self.env["account.account"]._fields.get("account_type")
        if not account_type_field:
            return

        selection = account_type_field.selection
        if callable(selection):
            selection = selection(self.env)

        for index, (code, label) in enumerate(selection or [], start=1):
            record = self.search([("code", "=", code)], limit=1)
            values = {"name": label, "sequence": index}
            if record:
                record.write(values)
            else:
                self.create({"code": code, **values})

    @api.model
    def _register_hook(self):
        res = super()._register_hook()
        self.sudo()._sync_from_account_type_selection()
        return res


class AccountAccountCompat(models.Model):
    _inherit = "account.account"

    user_type_id = fields.Many2one(
        "account.account.type",
        string="Account Type (Legacy)",
        compute="_compute_user_type_id_compat",
        search="_search_user_type_id_compat",
    )
    internal_type = fields.Char(
        string="Internal Type (Legacy)",
        compute="_compute_internal_type_compat",
    )

    @api.depends("account_type")
    def _compute_user_type_id_compat(self):
        compat_model = self.env["account.account.type"].sudo()
        code_to_record = {
            rec.code: rec
            for rec in compat_model.search(
                [("code", "in", list(set(self.mapped("account_type"))))]
            )
        }
        for account in self:
            account.user_type_id = code_to_record.get(account.account_type)

    @api.model
    def _search_user_type_id_compat(self, operator, value):
        allowed = {"=", "in", "!=", "not in"}
        if operator not in allowed:
            return []

        if operator in {"=", "!="}:
            ids = [value] if value else []
        else:
            ids = value or []

        codes = self.env["account.account.type"].sudo().browse(ids).mapped("code")
        if not codes:
            return [("id", "=", 0)] if operator in {"=", "in"} else []
        return [("account_type", operator, codes)]

    @api.depends("account_type")
    def _compute_internal_type_compat(self):
        mapping = {
            "asset_receivable": "receivable",
            "liability_payable": "payable",
            "asset_cash": "liquidity",
            "income": "other",
            "income_other": "other",
            "expense": "other",
            "expense_depreciation": "other",
            "expense_direct_cost": "other",
            "asset_current": "other",
            "asset_non_current": "other",
            "asset_prepayments": "other",
            "asset_fixed": "other",
            "liability_current": "other",
            "liability_non_current": "other",
            "equity": "other",
            "equity_unaffected": "other",
            "off_balance": "other",
        }
        for account in self:
            account.internal_type = mapping.get(account.account_type, "other")
