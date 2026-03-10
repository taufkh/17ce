# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class Meeting(models.Model):
    _name = "calendar.event"
    # v16: timer.mixin is Enterprise-only; removed from _inherit for Community
    _inherit = ["calendar.event"]

    @api.onchange('type')
    def _onchange_type(self):
        self.meeting_type = False
        self.site = False

    type = fields.Selection([('meeting', 'Meeting'), ('task', 'Task')], string='Type', default='meeting')
    meeting_type = fields.Selection([('internal', 'Internal'), ('external', 'External')], string='Meeting Type')
    site = fields.Selection([('onsite', 'Onsite'), ('remote', 'Remote')], string='Site')
    requirement_id = fields.Many2one('odes.crm.requirement', string='Requirement')
    manhours = fields.Integer(string='Manhours (Legacy)')
    # manhours = fields.Float(string='Manhours',digits=(2,1))
    manhours2 = fields.Float(string='Manhours', digits=(2,1))
    is_done = fields.Boolean(string='Done')
    meeting_id = fields.Many2one(comodel_name='calendar.event', string='Meeting')
    task_ids = fields.One2many(comodel_name='calendar.event', inverse_name='meeting_id', string='Task')

    @api.model_create_multi
    def create(self, vals_list):
        records = super(Meeting, self).create(vals_list)
        for vals, rec in zip(vals_list, records):
            if vals.get('type') == 'task' and vals.get('meeting_id'):
                rec.write({'task_ids': [(4, vals['meeting_id'])]})
            if 'duration' in vals:
                rec.write({'manhours2': vals['duration']})
        return records

    @api.onchange('duration')
    def _onchange_duration(self):
        for ev in self:
            if ev.allday:
                ev.manhours2 = 8
            else:
                if ev.duration:
                    # ev.manhours = ev.duration  
                    ev.manhours2 = ev.duration      
            # else:
            #     ev.manhours = ev.manhours

    @api.onchange('allday')
    def _onchange_allday(self):
        for ev in self:
            if ev.allday:
                ev.manhours2 = 8
            else:
                if ev.duration:
                    ev.manhours2 = ev.duration
            # else:
            #     ev.manhours = ev.manhours

    """ Below is the field linked & related to Timesheet """
    # planned_hours = fields.Float(compute='_compute_planned_hours', string='Initially Planned Hours')
    planned_hours = fields.Float("Initially Planned Hours", compute='_compute_planned_hours', help='Time planned to achieve this task (including its sub-tasks).', tracking=True)
    # subtask_planned_hours = fields.Float("Sub-tasks Planned Hours", compute='_compute_subtask_planned_hours', help="Sum of the time planned of all the sub-tasks linked to this task. Usually less or equal to the initially time planned of this task.")
    analytic_account_active = fields.Boolean("Active Analytic Account", compute='_compute_analytic_account_active')
    allow_timesheets = fields.Boolean("Allow timesheets", related='requirement_id.project_id.allow_timesheets', help="Timesheets can be logged on this task.", readonly=True)
    remaining_hours = fields.Float("Remaining Hours", compute='_compute_remaining_hours', store=True, readonly=True, help="Total remaining time, can be re-estimated periodically by the assignee of the task.")
    effective_hours = fields.Float("Hours Spent", compute='_compute_effective_hours', compute_sudo=True, store=True, help="Time spent on this task, excluding its sub-tasks.")
    total_hours_spent = fields.Float("Total Hours", compute='_compute_total_hours_spent', store=True, help="Time spent on this task, including its sub-tasks.")
    progress = fields.Float("Progress", compute='_compute_progress_hours', store=True, group_operator="avg", help="Display progress of current task.")
    overtime = fields.Float(compute='_compute_progress_hours', store=True)
    # subtask_effective_hours = fields.Float("Sub-tasks Hours Spent", compute='_compute_subtask_effective_hours', store=True, help="Time spent on the sub-tasks (and their own sub-tasks) of this task.")
    timesheet_ids = fields.One2many('account.analytic.line', 'calendar_id', 'Timesheets')
    encode_uom_in_days = fields.Boolean(compute='_compute_encode_uom_in_days')
    # requirement_ids = fields.One2many(comodel_name='odes.crm.requirement', inverse_name='calendar_id', string='Requirements')
    project_requirement_ids = fields.Many2many(comodel_name='odes.crm.requirement', string='Requirements')

    @api.depends('duration')
    def _compute_planned_hours(self):
        for event in self:
            if event.duration:
                event.planned_hours = event.duration
            else:
                event.planned_hours = 0

    @api.depends('requirement_id.project_id.analytic_account_id.active')
    def _compute_analytic_account_active(self):
        """ Overridden in sale_timesheet """
        for event in self:
            event.analytic_account_active = event.requirement_id.project_id.analytic_account_id.active

    @api.depends('timesheet_ids.unit_amount')
    def _compute_effective_hours(self):
        for event in self:
            event.effective_hours = round(sum(event.timesheet_ids.mapped('unit_amount')), 2)

    @api.depends('effective_hours', 'planned_hours')
    def _compute_remaining_hours(self):
        for event in self:
            event.remaining_hours = event.planned_hours - event.effective_hours

    @api.depends('effective_hours')
    def _compute_total_hours_spent(self):
        for event in self:
            event.total_hours_spent = event.effective_hours

    @api.depends('effective_hours', 'planned_hours')
    def _compute_progress_hours(self):
        for event in self:
            if (event.planned_hours > 0.0):
                task_total_hours = event.effective_hours
                event.overtime = max(task_total_hours - event.planned_hours, 0)
                if task_total_hours > event.planned_hours:
                    event.progress = 100
                else:
                    event.progress = round(100.0 * task_total_hours / event.planned_hours, 2)
            else:
                event.progress = 0.0
                event.overtime = 0

    # @api.depends('child_ids.effective_hours', 'child_ids.subtask_effective_hours')
    # def _compute_subtask_effective_hours(self):
    #     for task in self:
    #         task.subtask_effective_hours = sum(child_task.effective_hours + child_task.subtask_effective_hours for child_task in task.child_ids)

    def _compute_encode_uom_in_days(self):
        self.encode_uom_in_days = self.env.company.timesheet_encode_uom_id == self.env.ref('uom.product_uom_day')

    # @api.depends('child_ids.planned_hours')
    # def _compute_subtask_planned_hours(self):
    #     for task in self:
    #         task.subtask_planned_hours = sum(child_task.planned_hours + child_task.subtask_planned_hours for child_task in task.child_ids)

    # v16: timer.mixin (Enterprise-only) fields and methods disabled below
    # display_timesheet_timer = fields.Boolean("Display Timesheet Time", compute='_compute_display_timesheet_timer')
    # display_timer_start_secondary = fields.Boolean(compute='_compute_display_timer_buttons')
    # _compute_display_timer_buttons, _compute_display_timesheet_timer,
    # action_timer_start, action_timer_stop, _action_open_new_timesheet all removed
