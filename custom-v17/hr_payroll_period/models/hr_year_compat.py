# Copyright 2026
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrYearCompat(models.Model):
    _name = "hr.year"
    _description = "HR Year (Compatibility)"
    _order = "date_start desc, id desc"

    name = fields.Char("HR Year", required=True)
    code = fields.Char("Code", required=True)
    date_start = fields.Date("Start Date", required=True)
    date_stop = fields.Date("End Date", required=True)
    state = fields.Selection(
        [("draft", "Draft"), ("open", "Open"), ("done", "Closed")],
        string="Status",
        default="draft",
        readonly=True,
        copy=False,
    )
