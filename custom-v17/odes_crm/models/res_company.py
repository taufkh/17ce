# -*- coding: utf-8 -*-
import xmlrpc.client
from odoo import api, fields, models, tools, _

class Company(models.Model):
    _inherit = 'res.company'

    def action_generate_req_num(self):
        requirements = self.env['odes.crm.requirement'].search([('number', '=', False)])
        for requirement in requirements:
            requirement.write({
                'number': self.env['ir.sequence'].next_by_code('odes.crm.requirement')	
            })

    def action_get_pms_task(self):
        # url = 'http://127.0.0.2:8069'
        # db = 'ODES_PMS_17_MAY'
        # username = 'admin'
        # key = '66cb9897bbb123ff4f7451fd3fc10712af36299e'

        # url = 'https://devteam.odes.com.sg'
        # db = 'ODES_PMS'
        # username = 'admin'
        # key = '0bb41aeca3668925bcb0ef99fd67260f102f9c68'

        param_obj = self.env['ir.config_parameter'].sudo()
        requirement_obj = self.env['odes.crm.requirement'].sudo()
        draft_requirement_obj = self.env['odes.crm.requirement.draft'].sudo()
        requirement_task_obj = self.env['odes.crm.requirement.task'].sudo()

        url = param_obj.get_param('odes_crm.pms_url') or False
        db = param_obj.get_param('odes_crm.pms_database') or False
        username = param_obj.get_param('odes_crm.pms_username') or False
        key = param_obj.get_param('odes_crm.pms_key') or False
        last_update = param_obj.get_param('odes_crm.pms_last_update') or False

        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, key, {})

        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        # res_ids = models.execute_kw(db, uid, key, 'project.task', 'search', [[['requirement_number', '!=', False], ['is_sync', '=', False]]], {'limit': 100})
        res_ids = models.execute_kw(db, uid, key, 'project.task', 'search', [[['requirement_number', '!=', False], ['is_sync', '=', False], ['end_date', '>=', '2023-07-01']]], {'limit': 30})
        tasks = models.execute_kw(db, uid, key, 'project.task', 'read', [res_ids], {'fields': ['name', 'module_id', 'requester_id', 'mandays', 'project_id', 'user_id', 'project_team_id', 'date_deadline', 'start_date', 'end_date', 'stage_id', 'requirement_number', 'write_date']})

        # print('==================== Res Ids ====================')
        # print(res_ids)
        # print('=================================================')

        if last_update:
            exist_res_ids = models.execute_kw(db, uid, key, 'project.task', 'search', [[['is_sync', '=', True], ['end_date', '>=', '2023-07-01'], ['write_date', '>=', last_update]]], {'limit': 30})
            exist_tasks = models.execute_kw(db, uid, key, 'project.task', 'read', [exist_res_ids], {'fields': ['name', 'module_id', 'requester_id', 'mandays', 'project_id', 'user_id', 'project_team_id', 'date_deadline', 'start_date', 'end_date', 'stage_id', 'requirement_number', 'pma_task_id']})

            for exist_task in exist_tasks:
                requirement = requirement_obj.search([('number', '=', exist_task['requirement_number'])], limit=1)
                draft_requirement = draft_requirement_obj.search([('number', '=', exist_task['requirement_number']), ('draft_req_state', '=', 'draft')], limit=1)
                task = requirement_task_obj.search([('pms_task_id', '=', exist_task['id'])], limit=1)
                # task = requirement_task_obj.search([('id', '=', exist_task['pma_task_id']), ('draft_requirement_id', '=', False)], limit=1)
                # draft_task = requirement_task_obj.search([('id', '=', exist_task['pma_task_id']), ('draft_requirement_id', '=', draft_requirement.id)])

                # print('==================== Task ====================')
                # print(task)
                # print('============================================\n\n\n\n')

                values = {
                    'name': exist_task.get('name') or False,
                    'module': exist_task.get('module_id') and exist_task['module_id'][1] or False,
                    'requester': exist_task.get('requester_id') and exist_task['requester_id'][1] or False,
                    'mandays': exist_task.get('mandays') or False,
                    'project': exist_task.get('project_id') and exist_task['project_id'][1] or False,
                    'user': exist_task.get('user_id') and exist_task['user_id'][1] or False,
                    'team': exist_task.get('project_team_id') and exist_task['project_team_id'][1] or False,
                    'date_deadline': exist_task.get('date_deadline') or False,
                    'start_date': exist_task.get('start_date') or False,
                    'end_date': exist_task.get('end_date') or False,
                    'stage': exist_task.get('stage_id') and exist_task['stage_id'][1] or False                    
                }

                if requirement:
                    values['requirement_id'] = requirement.id

                if draft_requirement:
                    values['draft_requirement_id'] = draft_requirement.id
                    # draft_task.write(values)

                task.write(values)

        param_obj.set_param('odes_crm.pms_last_update', fields.Datetime.now())

        for task in tasks:
            requirement = requirement_obj.search([('number', '=', task['requirement_number'])], limit=1)
            draft_requirement = draft_requirement_obj.search([('number', '=', task['requirement_number']), ('draft_req_state', '=', 'draft')], limit=1)

            is_task_exist = requirement_task_obj.search([('pms_task_id', '=', task['id'])], limit=1)

            if requirement and not is_task_exist:
                pma_task = self.env['odes.crm.requirement.task'].create({
                    'name': task.get('name') or False,
                    'module': task.get('module_id') and task['module_id'][1] or False,
                    'requester': task.get('requester_id') and task['requester_id'][1] or False,
                    'mandays': task.get('mandays') or False,
                    'project': task.get('project_id') and task['project_id'][1] or False,
                    'user': task.get('user_id') and task['user_id'][1] or False,
                    'team': task.get('project_team_id') and task['project_team_id'][1] or False,
                    'date_deadline': task.get('date_deadline') or False,
                    'start_date': task.get('start_date') or False,
                    'end_date': task.get('end_date') or False,
                    'stage': task.get('stage_id') and task['stage_id'][1] or False,
                    'pms_task_id': task.get('id') or False,
                    'requirement_id': requirement.id
                })
                models.execute_kw(db, uid, key, 'project.task', 'write', [task.get('id'), {'is_sync': True, 'pma_task_id': pma_task.id}])

            if draft_requirement and not is_task_exist:
                draft_pma_task = self.env['odes.crm.requirement.task'].create({
                    'name': task.get('name') or False,
                    'module': task.get('module_id') and task['module_id'][1] or False,
                    'requester': task.get('requester_id') and task['requester_id'][1] or False,
                    'mandays': task.get('mandays') or False,
                    'project': task.get('project_id') and task['project_id'][1] or False,
                    'user': task.get('user_id') and task['user_id'][1] or False,
                    'team': task.get('project_team_id') and task['project_team_id'][1] or False,
                    'date_deadline': task.get('date_deadline') or False,
                    'start_date': task.get('start_date') or False,
                    'end_date': task.get('end_date') or False,
                    'stage': task.get('stage_id') and task['stage_id'][1] or False,
                    'pms_task_id': task.get('id') or False,
                    'draft_requirement_id': draft_requirement.id
                })
                models.execute_kw(db, uid, key, 'project.task', 'write', [task.get('id'), {'is_sync': True, 'pma_task_id': draft_pma_task.id}])

    def action_resync_pms_task(self):
        # Key Local DEVTEAM_SERVER d8fc15166e3a492083067db0e12805b9c7635969
        # url = 'http://127.0.0.20:8069'
        # db = 'ODES_PMS_17_MAY'
        # username = 'admin'
        # key = '66cb9897bbb123ff4f7451fd3fc10712af36299e'

        # url = 'https://devteam.odes.com.sg'
        # db = 'ODES_PMS'
        # username = 'admin'
        # key = '0bb41aeca3668925bcb0ef99fd67260f102f9c68'
        param_obj = self.env['ir.config_parameter'].sudo()
        draft_requirement_obj = self.env['odes.crm.requirement.draft'].sudo()
        requirement_obj = self.env['odes.crm.requirement'].sudo()

        url = param_obj.get_param('odes_crm.pms_url') or False
        db = param_obj.get_param('odes_crm.pms_database') or False
        username = param_obj.get_param('odes_crm.pms_username') or False
        key = param_obj.get_param('odes_crm.pms_key') or False
        resync_from = param_obj.get_param('odes_crm.resync_from') or False

        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, key, {})

        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        res_ids = models.execute_kw(db, uid, key, 'project.task', 'search', [[['requirement_number', '!=', False], ['is_sync', '=', True], ['end_date', '>=', resync_from], '|', ['pma_task_id', '=', False], ['pma_task_id', '=', 0]]])
        tasks = models.execute_kw(db, uid, key, 'project.task', 'read', [res_ids], {'fields': ['name', 'module_id', 'requester_id', 'mandays', 'project_id', 'user_id', 'project_team_id', 'date_deadline', 'start_date', 'end_date', 'stage_id', 'requirement_number', 'write_date']})

        for task in tasks:
            requirement = requirement_obj.search([('number', '=', task['requirement_number'])], limit=1)
            """ 
                Draft Requirement yang udah di confirm
                Ketika di Resync, akan terbuat lagi (?)
            """
            if requirement:
                pma_task = self.env['odes.crm.requirement.task'].create({
                    'name': task.get('name') or False,
                    'module': task.get('module_id') and task['module_id'][1] or False,
                    'requester': task.get('requester_id') and task['requester_id'][1] or False,
                    'mandays': task.get('mandays') or False,
                    'project': task.get('project_id') and task['project_id'][1] or False,
                    'user': task.get('user_id') and task['user_id'][1] or False,
                    'team': task.get('project_team_id') and task['project_team_id'][1] or False,
                    'date_deadline': task.get('date_deadline') or False,
                    'start_date': task.get('start_date') or False,
                    'end_date': task.get('end_date') or False,
                    'stage': task.get('stage_id') and task['stage_id'][1] or False,
                    'pms_task_id': task.get('id') or False,
                    'requirement_id': requirement.id
                })
                models.execute_kw(db, uid, key, 'project.task', 'write', [task.get('id'), {'is_sync': True, 'pma_task_id': pma_task.id}])

            draft_requirement = draft_requirement_obj.search([('number', '=', task['requirement_number'])], limit=1)
            if draft_requirement:
                draft_pma_task = self.env['odes.crm.requirement.task'].create({
                    'name': task.get('name') or False,
                    'module': task.get('module_id') and task['module_id'][1] or False,
                    'requester': task.get('requester_id') and task['requester_id'][1] or False,
                    'mandays': task.get('mandays') or False,
                    'project': task.get('project_id') and task['project_id'][1] or False,
                    'user': task.get('user_id') and task['user_id'][1] or False,
                    'team': task.get('project_team_id') and task['project_team_id'][1] or False,
                    'date_deadline': task.get('date_deadline') or False,
                    'start_date': task.get('start_date') or False,
                    'end_date': task.get('end_date') or False,
                    'stage': task.get('stage_id') and task['stage_id'][1] or False,
                    'pms_task_id': task.get('id') or False,
                    'draft_requirement_id': draft_requirement.id
                })
                models.execute_kw(db, uid, key, 'project.task', 'write', [task.get('id'), {'is_sync': True, 'pma_task_id': draft_pma_task.id}])

    def action_resync_duplicate_pms_task(self):
        # url = 'http://127.0.0.20:8069'
        # db = 'ODES_PMS_17_MAY'
        # username = 'admin'
        # key = '66cb9897bbb123ff4f7451fd3fc10712af36299e'

        # url = 'https://devteam.odes.com.sg'
        # db = 'ODES_PMS'
        # username = 'admin'
        # key = '0bb41aeca3668925bcb0ef99fd67260f102f9c68'
        param_obj = self.env['ir.config_parameter'].sudo()
        requirement_obj = self.env['odes.crm.requirement'].sudo()

        url = param_obj.get_param('odes_crm.pms_url') or False
        db = param_obj.get_param('odes_crm.pms_database') or False
        username = param_obj.get_param('odes_crm.pms_username') or False
        key = param_obj.get_param('odes_crm.pms_key') or False
        resync_from = param_obj.get_param('odes_crm.resync_from') or False

        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, key, {})

        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        res_ids = models.execute_kw(db, uid, key, 'project.task', 'search', [[['requirement_number', '!=', False], ['is_sync', '=', True], ['end_date', '>=', resync_from], '|', ['pma_task_id', '=', False], ['pma_task_id', '=', 0]]])
        tasks = models.execute_kw(db, uid, key, 'project.task', 'read', [res_ids], {'fields': ['name', 'module_id', 'requester_id', 'mandays', 'project_id', 'user_id', 'project_team_id', 'date_deadline', 'start_date', 'end_date', 'stage_id', 'requirement_number', 'write_date']})

        for task in tasks:
            requirement = requirement_obj.search([('number', '=', task['requirement_number'])], limit=1)
            if requirement:
                pma_task = self.env['odes.crm.requirement.task'].create({
                    'name': task.get('name') or False,
                    'module': task.get('module_id') and task['module_id'][1] or False,
                    'requester': task.get('requester_id') and task['requester_id'][1] or False,
                    'mandays': task.get('mandays') or False,
                    'project': task.get('project_id') and task['project_id'][1] or False,
                    'user': task.get('user_id') and task['user_id'][1] or False,
                    'team': task.get('project_team_id') and task['project_team_id'][1] or False,
                    'date_deadline': task.get('date_deadline') or False,
                    'start_date': task.get('start_date') or False,
                    'end_date': task.get('end_date') or False,
                    'stage': task.get('stage_id') and task['stage_id'][1] or False,
                    'pms_task_id': task.get('id') or False,
                    'requirement_id': requirement.id
                })
                models.execute_kw(db, uid, key, 'project.task', 'write', [task.get('id'), {'is_sync': True, 'pma_task_id': pma_task.id}])

    def _default_nda_content(self):
        return """
            <ol type="I"><li><p>THE PARTIES. This Non-Disclosure Agreement, hereinafter known as the “Agreement”, created on ___________________, 20____ is by and between ___________________, hereinafter known as “1st Party”, and ___________________, hereinafter known as “2nd Party”, and collectively known as the “Parties”. WHEREAS, this Agreement is created for the purpose of preventing the unauthorized disclosure of the confidential and proprietary information. The Parties agree as follows:</p></li><li><p>TYPE OF AGREEMENT. (check one) ☐ - Unilateral. This Agreement shall be Unilateral, whereas, 1st Party shall have sole ownership of the Confidential Information with 2nd Party being prohibited from disclosing confidential and proprietary information that is to be released by the 1st Party. ☐ - Mutual. This Agreement shall be Mutual, whereas, the Parties shall be prohibited from disclosing confidential and proprietary information that is to be shared between one another.</p></li></ol>
        """

    nda_content = fields.Text('NDA Content', default=_default_nda_content)
    doc_config_ids = fields.One2many('odes.crm.doc.config', 'company_id', string='Doc. Default Configs')
