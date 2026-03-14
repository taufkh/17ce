# Copyright (C) 2021 Nimarosa (Nicolas Rodriguez) (<nicolasrsande@gmail.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        res = super().get_worked_day_lines(contracts, date_from, date_to)
        for contract in contracts.filtered(
            lambda contract: contract.resource_calendar_id
        ):
            # only use payslip day_from if it's greather than contract start date
            if date_from < contract.date_start:
                date_from = contract.date_start
            # == compute public holidays == #
            pholidays = self._compute_public_holidays_days(contract, date_from, date_to)
            if pholidays["number_of_days"] > 0:
                res.append(pholidays)
        return res

    def _compute_public_holidays_days(self, contract, date_from, date_to):
        ph_days = self._get_public_holidays_days(contract, date_from, date_to)
        ph_hours = (
            ph_days * 8
        )  # Use 8 as default value if employee has no resource_calendar
        if contract.employee_id.resource_calendar_id:
            ph_hours = ph_days * contract.employee_id.resource_calendar_id.hours_per_day
        return {
            "name": _("Public Holidays Leaves"),
            "sequence": 10,
            "code": "PHOL",
            "number_of_days": ph_days,
            "number_of_hours": ph_hours,
            "contract_id": contract.id,
        }

    def _get_public_holidays_days(self, contract, date_from, date_to):
        """Support both OCA and SG public-holiday models in Odoo 17 runtime."""
        if "hr.holidays.public" in self.env:
            public_holidays = self.env["hr.holidays.public"].get_holidays_list(
                year=date_from.year,
                start_dt=date_from,
                end_dt=date_to,
                employee_id=contract.employee_id.id,
            )
            return len(public_holidays)
        if "hr.holiday.public" in self.env and "hr.holiday.lines" in self.env:
            public_holiday_ids = self.env["hr.holiday.public"].search(
                [("name", "=", str(date_from.year))]
            )
            if not public_holiday_ids:
                return 0
            return self.env["hr.holiday.lines"].search_count(
                [
                    ("holiday_id", "in", public_holiday_ids.ids),
                    ("holiday_date", ">=", date_from),
                    ("holiday_date", "<=", date_to),
                ]
            )
        return 0
