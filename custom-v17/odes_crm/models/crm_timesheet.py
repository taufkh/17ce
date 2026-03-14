# -*- coding: utf-8 -*-
from lxml import etree
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    calendar_id = fields.Many2one(
        'calendar.event', 'Calendar', compute='_compute_project_calendar_id', store=True, readonly=False, index=True,
        domain="[('requirement_id.project_id.allow_timesheets', '=', True), ('requirement_id.project_id', '=?', project_id)]")

    @api.depends('calendar_id', 'calendar_id.requirement_id.project_id', 'project_id')
    def _compute_project_calendar_id(self):
        for line in self.filtered(lambda line: not line.project_id):
            line.project_id = line.task_id.project_id
        for line in self.filtered(lambda line: not line.project_id and line.project_id != line.calendar_id.requirement_id.project_id):
            line.calendar_id = False