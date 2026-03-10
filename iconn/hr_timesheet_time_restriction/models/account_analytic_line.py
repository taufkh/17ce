# Copyright 2022 Dinar Gabbasov
# Copyright 2022 Ooops404
# Copyright 2022 Cetmix
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, models, fields
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    def _check_timesheet_week(self, ts_date):
        """Allow only current week (Monday–Sunday)"""
        if not ts_date:
            return
        
        # Konversi kalau masih string
        if isinstance(ts_date, str):
            ts_date = fields.Date.from_string(ts_date)

        if self.user_has_groups(
            "hr_timesheet.group_timesheet_manager"
        ):
            return

        today = fields.Date.context_today(self)
        monday_this_week = today - relativedelta(days=today.weekday())
        sunday_this_week = monday_this_week + relativedelta(days=6)

        msg_error = "You can only create, edit, or delete timesheets for the current week (Monday–Sunday)."
        if ts_date < monday_this_week:
            raise ValidationError(
                _(msg_error)
            )

        if ts_date > sunday_this_week:
            raise ValidationError(
                _(msg_error)
            )

    @api.model
    def create(self, vals):
        self._check_timesheet_week(vals.get("date"))
        return super().create(vals)

    def write(self, vals):
        for record in self:
            self._check_timesheet_week(record.date)

        return super().write(vals)

    def unlink(self):
        for record in self:
            self._check_timesheet_week(record.date)

        return super().unlink()
