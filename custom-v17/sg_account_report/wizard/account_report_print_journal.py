# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountPrintJournal(models.TransientModel):
    _name = "account.print.journal"
    _description = "Journals Audit (Compatibility)"
    _inherit = "account.common.report"

    amount_currency = fields.Boolean(string="With Currency")
    sort_selection = fields.Selection(
        [("l.date", "Date"), ("am.name", "Journal Entry Number")],
        string="Entries Sorted by",
        required=True,
        default="am.name",
    )

    def pre_print_report(self, data):
        data = super().pre_print_report(data)
        data["form"].update(self.read(["amount_currency", "sort_selection"])[0])
        return data

    def _print_report(self, data):
        action = self.env.ref("account.action_report_journal", raise_if_not_found=False)
        if action:
            return action.report_action(self, data=data)
        return {"type": "ir.actions.act_window_close"}
