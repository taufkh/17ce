from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class DateRangeType(models.Model):
    _name = "date.range.type"
    _description = "Date Range Type"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", string="Company")
    allow_overlap = fields.Boolean(default=False)
    active = fields.Boolean(default=True)


class DateRange(models.Model):
    _name = "date.range"
    _description = "Date Range"
    _order = "date_start, id"

    name = fields.Char(required=True)
    type_id = fields.Many2one("date.range.type", required=True, ondelete="restrict")
    company_id = fields.Many2one("res.company", string="Company")
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_start > rec.date_end:
                raise UserError("Start date cannot be after end date.")


class DateRangeGenerator(models.TransientModel):
    _name = "date.range.generator"
    _description = "Date Range Generator"

    name_prefix = fields.Char(required=True)
    date_start = fields.Date(required=True)
    type_id = fields.Many2one("date.range.type", required=True, ondelete="restrict")
    company_id = fields.Many2one("res.company", string="Company")
    unit_of_time = fields.Char(required=True, default="1")
    duration_count = fields.Integer(required=True, default=1)
    count = fields.Integer(required=True, default=1)

    def _step_delta(self):
        self.ensure_one()
        unit = int(self.unit_of_time or 1)
        duration = max(1, int(self.duration_count or 1))
        if unit == 0:
            return relativedelta(years=duration)
        if unit == 1:
            return relativedelta(months=duration)
        if unit == 2:
            return relativedelta(weeks=duration)
        return relativedelta(days=duration)

    def _generate_date_ranges(self):
        self.ensure_one()
        start = fields.Date.to_date(self.date_start)
        if not start:
            return []

        total = max(1, int(round(self.count or 1)))
        step = self._step_delta()
        results = []
        for index in range(total):
            end = start + step - timedelta(days=1)
            vals = {
                "name": "%s %02d" % (self.name_prefix, index + 1),
                "type_id": self.type_id.id,
                "company_id": self.company_id.id if self.company_id else False,
                "date_start": start,
                "date_end": end,
            }
            results.append(vals)
            start = end + timedelta(days=1)
        return results

