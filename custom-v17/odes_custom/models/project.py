# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse

class ProjectProject(models.Model):
    _inherit = 'project.project'

    lead_id = fields.Many2one('crm.lead', 'Quotation', copy=False)

class Task(models.Model):
    _inherit = 'project.task'
    _order = "name, parent_id, id"

    task_color = fields.Integer('Task color', default=0)
    task_progress = fields.Float('Task Progress', digits=(16, 2))
    task_progressbar = fields.Float('Progress Bar', compute='_compute_task_progressbar', help='Display progress of current task.')
    task_color_render = fields.Char('Render Color')
    task_color_sel = fields.Selection([
        ('0', 'Teal'),
        ('1', 'Red'),
        ('2', 'Orange'),
        ('3', 'Yellow'),
        ('4', 'Light Blue'),
        ('5', 'Medium Blue'),
        ('6', 'Light Pink'),
        ('7', 'Dark Blue'),
        ('8', 'Gray'),
        ('9', 'Pink'),
        ('10', 'Aquamarine'),
        ('11', 'Purple'),
    ], 'Color', default='0')

    event_ids = fields.One2many('calendar.event', 'task_id', 'Meetings')
    meeting_count = fields.Integer('# Meetings', compute='_compute_meeting_count')

    def _compute_task_progressbar(self):
        for task in self:
            task.task_progressbar = task.task_progress

    @api.onchange('task_color_sel')
    def _set_color(self):
        if self.task_color_sel == '0':
            self.task_color = 0
            self.task_color_render = '#72969F'

        elif self.task_color_sel == '1':
            self.task_color = 1
            self.task_color_render = '#F7A298'

        elif self.task_color_sel == '2':
            self.task_color = 2
            self.task_color_render = '#F9CAA2'

        elif self.task_color_sel == '3':
            self.task_color = 3
            self.task_color_render = '#FBE279'

        elif self.task_color_sel == '4':
            self.task_color = 4
            self.task_color_render = '#A8DBF5'

        elif self.task_color_sel == '5':
            self.task_color = 5
            self.task_color_render = '#8CCFDC'

        elif self.task_color_sel == '6':
            self.task_color = 6
            self.task_color_render = '#EDAEAE'

        elif self.task_color_sel == '7':
            self.task_color = 7
            self.task_color_render = '#81B6C2'

        elif self.task_color_sel == '8':
            self.task_color = 8
            self.task_color_render = '#929BAF'

        elif self.task_color_sel == '9':
            self.task_color = 9
            self.task_color_render = '#E772A0'

        elif self.task_color_sel == '10':
            self.task_color = 10
            self.task_color_render = '#83DBB4'

        elif self.task_color_sel == '11':
            self.task_color = 11
            self.task_color_render = '#BFA4D5'

    @api.onchange('task_progress')
    def _onchange_task_progress(self):
        if self.task_progress > 100:
            raise UserError(_('Please enter a number from 0 to 100'))
        elif self.task_progress < 0:
            raise UserError(_('Please enter a number from 0 to 100'))

    def action_schedule_meeting(self):
        """ Open meeting's calendar view to schedule meeting on current opportunity.
            :return dict: dictionary value for created Meeting view
        """
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("calendar.action_calendar_event")
        partner_ids = self.env.user.partner_id.ids
        if self.partner_id:
            partner_ids.append(self.partner_id.id)

        if action['domain']:
            action['domain'].append(('task_id', '=', self.id)) 
        else:
            action['domain'] = [('task_id', '=', self.id)]

        action['context'] = {
            'default_task_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_partner_ids': partner_ids,
            'default_name': self.name,
            'event_ids.task_id': self.id
        }
        return action

    def _compute_meeting_count(self):
        for task in self:
            task.meeting_count = len(task.event_ids.ids) or 0
