# import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.tools import pycompat, DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT

class AmalgamationReportWizard(models.TransientModel):
    _name = 'amalgamation.report.wizard'
    _description = 'Amalgamation Report Wizard'

    @api.model
    def _compute_is_c_level(self):
        c_level_users = self.env.ref('odes_crm.group_odes_c_level').sudo().users.ids
        ctx = self._context or {}
        uid = ctx.get('uid')
        self.is_c_level = uid in c_level_users

    # Function to go to pivot views of requirement
    def action_view_amalgamation_report(self):
        self.ensure_one()

        # if not self.user_id:
        #     notification = {
        #         'type': 'ir.actions.client',
        #         'tag': 'display_notification',
        #         'params': {
        #             'title': ('Unable to process request'),
        #             'message': 'Please fill in the project manager fields',
        #             'type':'warning',  #types: success,warning,danger,info
        #             'sticky': False,  #True/False will display for few seconds if false
        #         },
        #     }
        #     return notification

        projects = self.env['project.project'].search([('user_id', '=', self.user_id.id)])

        project_list = []
        for project in projects:
            project_list.append(project.id)
        domain = []
        if self.user_id:
            domain = [('project_id', 'in',  project_list)]
        context = {'search_default_project': 1, 'search_default_stage': 1, 'search_default_status': 1, 'search_default_business_function': 1}

        return {
            'name': 'Amalgamation Report',
            'type': 'ir.actions.act_window',
            'view_mode': 'gantt',
            'res_model': 'odes.crm.requirement',
            'domain': domain,
            'context': context
        }

    def action_view_full_amalgamation_report(self):
        self.ensure_one()

        context = {'search_default_project': 1, 'search_default_stage': 1, 'search_default_status': 1, 'search_default_business_function': 1}

        return {
            'name': 'Amalgamation Report',
            'type': 'ir.actions.act_window',
            'view_mode': 'gantt',
            'res_model': 'odes.crm.requirement',
            'context': context
        }

    user_id = fields.Many2one(comodel_name='res.users', string='Project Manager')
    is_c_level = fields.Boolean(string='Is C Level', compute=_compute_is_c_level)
    
    
