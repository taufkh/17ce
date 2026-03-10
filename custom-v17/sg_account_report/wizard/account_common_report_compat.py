from odoo import api, fields, models


class AccountCommonReport(models.TransientModel):
    _name = "account.common.report"
    _description = "Account Common Report (Compatibility)"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    journal_ids = fields.Many2many(
        "account.journal",
        string="Journals",
        default=lambda self: self._default_journal_ids(),
    )
    chart_account_id = fields.Many2one(
        "account.account",
        string="Account",
        domain="[('company_id', '=', company_id)]",
    )
    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")
    target_move = fields.Selection(
        [("posted", "All Posted Entries"), ("all", "All Entries")],
        string="Target Moves",
        required=True,
        default="posted",
    )

    @api.model
    def _default_journal_ids(self):
        return self.env["account.journal"].search(
            [("company_id", "=", self.env.company.id)]
        )

    def _build_contexts(self, data):
        form = data.get("form", {})
        return {
            "journal_ids": form.get("journal_ids", []),
            "state": form.get("target_move", "all"),
            "date_from": form.get("date_from"),
            "date_to": form.get("date_to"),
            "strict_range": bool(form.get("date_from") or form.get("date_to")),
        }

    def pre_print_report(self, data):
        return data

    def check_report(self):
        self.ensure_one()
        data = {
            "ids": self._context.get("active_ids", []),
            "model": self._context.get("active_model", "ir.ui.menu"),
        }
        form = self.read(
            [
                "company_id",
                "journal_ids",
                "chart_account_id",
                "date_from",
                "date_to",
                "target_move",
            ]
        )[0]
        form["used_context"] = self._build_contexts({"form": form})
        data["form"] = form
        data = self.pre_print_report(data)
        return self._print_report(data)

    def _print_report(self, data):
        return {"type": "ir.actions.act_window_close"}

