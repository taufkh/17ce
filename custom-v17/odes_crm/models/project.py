# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from ast import literal_eval
from datetime import datetime

class Project(models.Model):
    _inherit = 'project.project'

    def get_gantt_project_details(self, payload):
        project_list = self.env['project.project'].sudo().search([('id', 'in', payload)])
        if len(project_list) != 0:
            data = {}
            for project in project_list:
                developer = [dev.name for dev in project.developer_ids if dev]
                data[project.name] = {
                    "dev": ' & '.join(developer),
                    "budgeted": project.credited_mandays,
                    "consumed": project.dev_consumed_mandays
                }
            return data

    def action_create_meeting(self):
        self.ensure_one()
        
        return {
            'name': 'Calendar',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'calendar.event',
            'target': 'new',
        }

    def action_view_meetings(self):
        self.ensure_one()
        domain = [('project_requirement_ids', '!=', False)]
        return {
            'name': 'Meetings',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'calendar.event',
            'domain': domain,
        }

    def action_view_requirement(self):
        self.ensure_one()

        domain = [('project_id', '=', self.id)]
        context = {'default_project_id': self.id, 'search_default_stage': 1, 'search_default_status': 1, 'search_default_business_function': 1, 'default_internal_member_ids': [user.id for user in self.internal_user_ids]}

        if self.lead_id:
            if self.lead_id.order_ids:
                domain = ['|', ('order_id', 'in', self.lead_id.order_ids._ids), ('project_id', '=', self.id)]
                context['default_order_id'] = self.lead_id.order_ids[0].id

                if self.lead_id.order_ids[0].pm_user_id and (self.lead_id.order_ids[0].pm_user_id != self.user_id):
                    self.write({
                        'user_id': self.lead_id.order_ids[0].pm_user_id.id    
                    })

        # Info Cyrus we found a workaround to only refresh requirement in a project
        return {
            'name': self.name + ' Requirements',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form,gantt',
            'res_model': 'odes.crm.requirement',
            'domain': domain,
            'context': context
        }

        # action_requirement = self.env.ref('odes_crm.action_odes_crm_requirement')
        # action = action_requirement.read()[0]
        # action['domain'] = domain
        # action['context'] = context
        # action['display_name'] = self.name + " Requirements"
        # return action

    def action_view_draft_requirement(self):
        self.ensure_one()

        domain = ['&', ('project_id', '=', self.id), ('draft_req_state', '=', 'draft')]
        context = {'default_project_id': self.id, 'default_internal_member_ids': [user.id for user in self.internal_user_ids]}

        if self.lead_id:
            if self.lead_id.order_ids:
                domain = ['&', '|', ('order_id', 'in', self.lead_id.order_ids._ids), ('project_id', '=', self.id), ('draft_req_state', '=', 'draft')]
                context['default_order_id'] = self.lead_id.order_ids[0].id

                if self.lead_id.order_ids[0].pm_user_id and (self.lead_id.order_ids[0].pm_user_id != self.user_id):
                    self.write({
                        'user_id': self.lead_id.order_ids[0].pm_user_id.id    
                    })

        return {
            'name': self.name + ' Draft Requirements',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'odes.crm.requirement.draft',
            'domain': domain,
            'context': context
        }

    def action_view_business_function(self):
        self.ensure_one()

        domain = [('project_id', '=', self.id)]
        context = {'default_project_id': self.id}

        if self.lead_id:
            if self.lead_id.order_ids:
                domain = ['|', '&', ('order_id', 'in', self.lead_id.order_ids._ids), ('order_id', '!=', False), '&', ('project_id', '=', self.id), ('project_id', '!=', False)]
                context['default_order_id'] = self.lead_id.order_ids[0].id

        return {
            'name': 'Business Functions',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'odes.crm.business.function',
            'domain': domain,
            'context': context
        }

    def action_view_developer_task(self):
        self.ensure_one()

        domain = [('requirement_id.project_id', '=', self.id)]
        # context = {'requirement_id.project_id.default_project_id': self.id}

        return {
            'name': 'Dev Task',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form,gantt',
            'res_model': 'odes.crm.requirement.task',
            'domain': domain,
            'context': {'search_default_group_module': 1, 'search_default_group_req': 1, 'search_default_group_stage': 1}
        }

    def action_view_pm_task(self):
        self.ensure_one()

        domain = [('requirement_id.project_id', '=', self.id)]
        pm_task_tree_views = self.env.ref('odes_crm.pm_task_calendar_event_tree_views').id
        pm_task_form_views = self.env.ref('calendar.view_calendar_event_form').id
        rec = self.env['calendar.event'].search([], limit=1)

        return {
            'name': self.name + ' PM Task',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_id': rec.id,
            'res_model': 'calendar.event',
            'views': [[pm_task_tree_views, "tree"], [pm_task_form_views, "form"]],
            'domain': domain,
        }
            # 'view_id': pm_task_views,
        # 'context': {'search_default_group_module': 1, 'search_default_group_req': 1, 'search_default_group_stage': 1}

    @api.depends('company_id')
    def _compute_is_requirement_visible(self):
        for project in self:
            param_company_id = literal_eval(self.env['ir.config_parameter'].sudo().get_param('odes_crm.crm_create_user_company_id', 'False'))
            project.is_requirement_visible = (project.company_id.id == param_company_id) and True or False

    def _compute_requirement_count(self):
        requirement_obj = self.env['odes.crm.requirement']
        for project in self:
            if project.lead_id and project.lead_id.order_ids:
                project.requirement_count = requirement_obj.search_count([('state', 'in', ['new', 'client_confirmed', 'development']), '|', ('order_id', 'in', project.lead_id.order_ids._ids), ('project_id', '=', project.id)])
            else:
                project.requirement_count = requirement_obj.search_count([('state', 'in', ['new', 'client_confirmed', 'development']), ('project_id', '=', project.id)])

    def _compute_draft_requirement_count(self):
        requirement_obj = self.env['odes.crm.requirement.draft']
        for project in self:
            if project.lead_id and project.lead_id.order_ids:
                project.draft_requirement_count = requirement_obj.search_count([('draft_req_state', '=', 'draft'), '|', ('order_id', 'in', project.lead_id.order_ids._ids), ('project_id', '=', project.id)])
            else:
                project.draft_requirement_count = requirement_obj.search_count([('draft_req_state', '=', 'draft'), ('project_id', '=', project.id)])

    @api.depends('project_live_date')
    def _compute_display_project_live_date(self):
        for rec in self:
            if rec.project_live_date:
                rec.display_project_live_date = rec.project_live_date.strftime('%d %b %Y')
            else:
                rec.display_project_live_date = False
    
    @api.depends('odes_crm_requirement_ids')
    def _compute_project_progress(self):
        for project in self:
            if project.odes_crm_requirement_ids:
                total_mandays = 0
                total_outstanding_mandays = 0
                if project.odes_crm_requirement_ids.requirement_task_ids:
                    for task in project.odes_crm_requirement_ids.requirement_task_ids:
                        total_mandays += 1
                        if task.stage == "Done":
                            total_outstanding_mandays += 1
                    if total_outstanding_mandays != 0:
                        project.project_progress = total_outstanding_mandays / total_mandays
                    else:
                        project.project_progress = total_mandays
                else:
                    project.project_progress = 0.00
            else:
                project.project_progress = 0.00

    @api.depends('odes_crm_requirement_ids', 'odes_crm_requirement_ids.total_manhours')
    def _compute_consumed_mandays(self):
        for project in self:
            if project.odes_crm_requirement_ids:
                project.consumed_mandays = sum(req.total_manhours for req in project.odes_crm_requirement_ids)

    @api.depends('odes_crm_requirement_ids.consumed_mandays')
    def _compute_dev_consumed_mandays(self):
        for project in self:
            if project.odes_crm_requirement_ids:
                project.dev_consumed_mandays = sum(req.consumed_mandays for req in project.odes_crm_requirement_ids)

    @api.depends('credited_mandays', 'dev_consumed_mandays')
    def _compute_budgeted_mandays_left(self):
        for project in self:
            if project.credited_mandays and project.dev_consumed_mandays:
                project.budgeted_mandays_left = project.credited_mandays - project.dev_consumed_mandays
            else:
                project.budgeted_mandays_left = project.credited_mandays - project.dev_consumed_mandays

    @api.depends('consumed_mandays', 'dev_consumed_mandays')
    def _compute_total_project_mandays_consumed(self):
        for project in self:
            if project.consumed_mandays and project.dev_consumed_mandays:
                project.total_project_mandays_consumed = project.consumed_mandays + project.dev_consumed_mandays
            else:
                project.total_project_mandays_consumed = project.consumed_mandays or project.dev_consumed_mandays

    @api.depends('odes_crm_requirement_ids')
    def _compute_project_progress_percentage(self):
        """ 
            PROJECT, STAGE, REQUIREMENT
                1 Project Can Have Many Stage
                1 Stage Can Have Many Requirement
            Project_Count = 1 | For each project will count as 1
            Stage_Maximum_Percentage = 1 / Total Stages Indicates in Project
            --------------------------------------
            Requirement_Count  = X | value supposed to be counted per stages not from project
                e.g : Project got 30 Requirements on total, 
                        so we will need to consider it per stage like: 
                        Stage A got 10 Requirements on total, Stage B got 20 Requirements, and so on.
            Task_Done_Count = X | value is the total Done Task no matter its Dev or PM Task
            Total_Task_Count = X | Value is computed by Dev_Task_Count + PM_Task_Count
            --------------------------------------
            Requirement_Percentage = X 
                Each Requirement definitely will got 100% of Progress Percentage,
                it should be computed by Task_Done_Count / Total_Task_Count / Requirement_Count
            Stage_Percentage = X | Computed by Requirement_Percentage * Stage_Maximum_Percentage
            --------------------------------------
            Project Progress = X | it should be computed by each Stage_Percentage
        """
        req_obj = self.env['odes.crm.requirement'].sudo()
        # for project in self:
        #     project_percentage = 0
        #     if project.stages_ids:
        #         stage_indicated_to_count = 0
        #         for stage in project.stages_ids:
        #             requirement_stage = req_obj.search([('project_id', '=', project.id), ('stage_id.name', '=', stage.name)], limit=1)
        #             stage_indicated_to_count += len(requirement_stage)
        #             requirement = req_obj.search([('project_id', '=', project.id), ('stage_id.name', '=', stage.name)])
        #             requirement_count = len(requirement)
        #             stage_requirement_percentage = 0
        #             for req in requirement:
        #                 if req.stage_id.name == "SAM" or req.stage_id.name == 'sam' or req.stage_id.name == 'Sam':
        #                     project_maximum_percentage = 0.25
        #                 elif req.stage_id.name == "DEVELOPMENT" or req.stage_id.name == 'development' or req.stage_id.name == 'Development':
        #                     project_maximum_percentage = 0.5
        #                 elif req.stage_id.name == "UAT/TRAINING" or req.stage_id.name == 'uat/training' or req.stage_id.name == 'Uat/Training':
        #                     project_maximum_percentage = 0.75
        #                 else:
        #                     project_maximum_percentage = 1
        #                 requirement_percentage = 0
        #                 task_done_count = 0
        #                 total_task_count = 0
        #                 # kalau req gak ada task
        #                 # if true task_done_count += 1
        #                 if ((len(req.requirement_task_ids) <= 0) and (len(req.event_task_ids) <= 0)):
        #                     if req.is_requirement:
        #                         total_task_count += 1
        #                         task_done_count += 1 

        #                 if req.requirement_task_ids:
        #                     for task in req.requirement_task_ids:
        #                         total_task_count += 1
        #                         if task.stage == "Done":
        #                             task_done_count += 1
        #                 if req.event_task_ids:
        #                     for task in req.event_task_ids:
        #                         total_task_count += 1
        #                         if task.is_done:
        #                             task_done_count +=1

        #                 if total_task_count != 0: # Python doesn't allow to divide by zero which will return ZeroDivisionError
        #                     requirement_percentage += task_done_count / total_task_count / requirement_count  
        #                 stage_requirement_percentage += requirement_percentage
        #             project_percentage += stage_requirement_percentage 
        #         if stage_indicated_to_count != 0:
        #             project.project_progress_percentage = project_percentage * project_maximum_percentage / stage_indicated_to_count
        #         else:
        #             project.project_progress_percentage = project_percentage * project_maximum_percentage / 1
        #     else:
        #         project.project_progress_percentage = 0.0
        for project in self:
            project_percentage = 0
            project_count = 1
            stage_count = len(project.stages_ids)
            if stage_count != 0: # Python doesn't allow to divide by zero which will return ZeroDivisionError
                stage_maximum_percentage = project_count / stage_count
            if project.stages_ids:
                for stage in project.stages_ids:
                    requirement = req_obj.search([('project_id', '=', project.id), ('stage_id.name', '=', stage.name), '|', ('active', '=', False), ('active', '=', True)])
                    requirement_count = len(requirement)
                    stage_percentage = 0
                    project_maximum_percentage = 1
                    for req in requirement:
                        requirement_percentage = 0
                        task_done_count = 0
                        total_task_count = 0
                        if ((len(req.requirement_task_ids) <= 0) and (len(req.event_task_ids) <= 0)):
                            if req.is_requirement:
                                total_task_count += 1
                                task_done_count += 1 
                        if req.requirement_task_ids:
                            for task in req.requirement_task_ids:
                                total_task_count += 1
                                if task.stage == "Done":
                                    task_done_count += 1
                        if req.event_task_ids:
                            for task in req.event_task_ids:
                                total_task_count += 1
                                if task.is_done:
                                    task_done_count +=1
                        if total_task_count != 0: # Python doesn't allow to divide by zero which will return ZeroDivisionError
                            requirement_percentage += task_done_count / total_task_count / requirement_count  
                        stage_percentage += requirement_percentage * stage_maximum_percentage 
                    project_percentage += stage_percentage 
                project.project_progress_percentage = project_percentage
            else:
                project.project_progress_percentage = 0.0

    @api.depends('odes_crm_requirement_ids')
    def _compute_internal_project_progress_percentage(self):
        """ 
            REQUIREMENT, TASK
            Requirement_Count = X | value expect to be the total requirement in a project
            --------------------------------------
            Task_Done_Count = X | value is the total Done Task no matter its Dev or PM Task per Req
            Total_Task_Count = X | Value is computed by Dev_Task_Count + PM_Task_Count per Req
            --------------------------------------
            Requirement_Percentage = X | value will be computed by Task_Done_Count / Total_Task_Count
            Requirement_Done_Percentage = X | value will be computed by all Requirement_Percentage
            --------------------------------------
            Project_Progress = X | value equals to Requirment_Done_Percentage / Requirement_Count
        """

        for project in self:
            if project.odes_crm_requirement_ids:
                requirement_done_percentage = 0
                requirement_count = len(project.odes_crm_requirement_ids)
                for req in project.odes_crm_requirement_ids:
                    requirement_percentage = 0
                    task_done_count = 0
                    total_task_count = 0
                    # kalau req gak ada task
                    # if true task_done_count += 1
                    if ((len(req.requirement_task_ids) <= 0) and (len(req.event_task_ids) <= 0)):
                        if req.is_requirement:
                            total_task_count += 1
                            task_done_count += 1 
                    if req.requirement_task_ids:
                        for task in req.requirement_task_ids:
                            total_task_count += 1
                            if task.stage == "Done":
                                task_done_count += 1
                    if req.event_task_ids:
                        for task in req.event_task_ids:
                            total_task_count += 1
                            if task.is_done:
                                task_done_count +=1
                    if total_task_count != 0: # Python doesn't allow to divide by zero which will return ZeroDivisionError
                        requirement_percentage += task_done_count / total_task_count
                    requirement_done_percentage += requirement_percentage
                # project_percentage += requirement_done_percentage
                project.internal_project_progress_percentage = requirement_done_percentage / requirement_count
            else:
                project.internal_project_progress_percentage = 0.0

    is_requirement_visible = fields.Boolean(compute='_compute_is_requirement_visible', string='Requirement Visible')
    customer_user_ids = fields.Many2many('res.users', 'project_project_customer_user_rel', 'project_id', 'user_id', string='Customer Users')
    odes_crm_requirement_ids = fields.One2many('odes.crm.requirement', 'project_id', string='Requirements')
    project_type = fields.Selection([('external', 'External'), ('internal', 'Internal')], default='external', string='Project Type')
    requirement_count = fields.Integer(compute='_compute_requirement_count', string='Number of Outstanding Requirements')
    draft_requirement_count = fields.Integer(compute='_compute_draft_requirement_count', string='Number of Outstanding Draft Requirements')
    project_live_date = fields.Date(string='Target Live Date')
    display_project_live_date = fields.Char(compute='_compute_display_project_live_date', string='Display Project Live Date')
    project_progress = fields.Float(compute='_compute_project_progress', string='Progress')
    project_progress_percentage = fields.Float(compute='_compute_project_progress_percentage', string='External Progress')
    internal_project_progress_percentage = fields.Float(compute='_compute_internal_project_progress_percentage', string='Internal Progress')
    credited_mandays = fields.Float(string='Total Budgeted Mandays', digits=(16,3))
    # PM Consumed
    consumed_mandays = fields.Float(compute='_compute_consumed_mandays', string='Total Consumed Mandays', digits=(16,3), store=True)
    # Developer Consumed
    dev_consumed_mandays = fields.Float(compute='_compute_dev_consumed_mandays', string='Dev Completed Mandays', digits=(16,3), store=True)
    # Mandays Left
    budgeted_mandays_left = fields.Float(compute='_compute_budgeted_mandays_left', string='Budgeted Mandays Left', digits=(16,3))
    total_project_mandays_consumed = fields.Float(compute='_compute_total_project_mandays_consumed', string='Total Project Mandays Consumed', digits=(16,3))
    developer_ids = fields.Many2many(comodel_name='odes.crm.requirement.developers', string='Developer')
    internal_user_ids = fields.Many2many(comodel_name='res.users', string='Internal Members')
    # stages_ids = fields.Many2many(string="Stage", comodel_name='odes.crm.requirement.type')
    stages_ids = fields.Many2many('odes.crm.requirement.type', 'odes_crm_requirement_type_rel', 'project_id', 'type_id', string='Requirement Stages')
    # project_stage_maximum_percentage = fields.Float(compute='_compute_project_stage_maximum_percentage', string='Project Stage Maximum Percentage')
    
    # @api.depends('stages_ids')
    # def _compute_project_stage_maximum_percentage(self):
    #     for project in self:
    #         if project.stages_ids:
    #             project.project_stage_maximum_percentage = 1 / len(project.stages_ids)
# class ProjectTask(models.Model):
#     _inherit = 'project.task'

#     display_planned_date_begin = fields.Char(compute='_compute_display_planned_date_begin', string='Display PLanned Date Begin')
#     display_planned_date_end = fields.Char(compute='_compute_display_planned_date_end', string='Display Planned Date End')
#     display_date_deadline = fields.Char(compute='_compute_display_date_deadline', string='Display Date Deadline')
#     display_manhours = fields.Integer(compute='_compute_display_manhours', string='Manhours')
    
#     @api.depends('event_ids.manhours')
#     def _compute_display_manhours(self):
#         for rec in self:
#             if rec.event_ids:
#                 for ev in rec.event_ids:
#                     if ev.manhours:
#                         rec.display_manhours += ev.manhours
#                     else:
#                         rec.display_manhours = False
#             else:
#                 rec.display_manhours = False

#     @api.depends('date_deadline')
#     def _compute_display_date_deadline(self):
#         for rec in self:
#             if rec.date_deadline:
#                 rec.display_date_deadline = rec.date_deadline.strftime('%d %b %Y')
#             else:
#                 rec.display_date_deadline = False

#     @api.depends('planned_date_end')
#     def _compute_display_planned_date_end(self):
#         for rec in self:
#             if rec.planned_date_end:
#                 rec.display_planned_date_end = rec.planned_date_end.strftime('%d %b %Y')
#             else:
#                 rec.display_planned_date_end = False

#     @api.depends('planned_date_begin')
#     def _compute_display_planned_date_begin(self):
#         for rec in self:
#             if rec.planned_date_begin:
#                 rec.display_planned_date_begin = rec.planned_date_begin.strftime('%d %b %Y')
#             else:
#                 rec.display_planned_date_begin = False
