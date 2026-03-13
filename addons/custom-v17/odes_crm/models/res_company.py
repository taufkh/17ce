# -*- coding: utf-8 -*-
import logging
import socket
import xmlrpc.client
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)

class Company(models.Model):
    _inherit = 'res.company'

    pms_simulation = fields.Boolean(
        string='PMS Simulation',
        compute='_compute_pms_simulation',
        inverse='_inverse_pms_simulation',
        help='If enabled, PMS cron runs in simulation mode (no external XML-RPC call).',
    )

    @api.depends()
    def _compute_pms_simulation(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'odes_crm.pms_simulation', default='0'
        )
        enabled = str(value).strip().lower() in ('1', 'true', 'yes', 'on')
        for company in self:
            company.pms_simulation = enabled

    def _inverse_pms_simulation(self):
        param_obj = self.env['ir.config_parameter'].sudo()
        for company in self:
            param_obj.set_param(
                'odes_crm.pms_simulation', '1' if company.pms_simulation else '0'
            )

    def action_generate_req_num(self):
        requirements = self.env['odes.crm.requirement'].search([('number', '=', False)])
        for requirement in requirements:
            requirement.write({
                'number': self.env['ir.sequence'].next_by_code('odes.crm.requirement')	
            })

    def _get_pms_rpc_context(self):
        param_obj = self.env['ir.config_parameter'].sudo()
        url = param_obj.get_param('odes_crm.pms_url') or False
        db = param_obj.get_param('odes_crm.pms_database') or False
        username = param_obj.get_param('odes_crm.pms_username') or False
        key = param_obj.get_param('odes_crm.pms_key') or False

        if not all([url, db, username, key]):
            _logger.warning(
                "PMS sync skipped: incomplete configuration (url/db/username/key)."
            )
            return False

        try:
            # Keep cron responsive when PMS endpoint is down/unreachable.
            previous_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(10)
            common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
            uid = common.authenticate(db, username, key, {})
            if not uid:
                _logger.warning("PMS sync skipped: authentication failed for '%s'.", url)
                return False
            models_proxy = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        except Exception as err:
            _logger.warning("PMS sync skipped: connection/auth error: %s", err)
            return False
        finally:
            socket.setdefaulttimeout(previous_timeout)

        return {
            'url': url,
            'db': db,
            'username': username,
            'key': key,
            'uid': uid,
            'models_proxy': models_proxy,
            'param_obj': param_obj,
        }

    def _is_pms_simulation_enabled(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'odes_crm.pms_simulation', default='0'
        )
        return str(value).strip().lower() in ('1', 'true', 'yes', 'on')

    def _simulate_pms_sync(self, action_name):
        requirement_count = self.env['odes.crm.requirement'].sudo().search_count([])
        draft_requirement_count = self.env['odes.crm.requirement.draft'].sudo().search_count([])
        task_count = self.env['odes.crm.requirement.task'].sudo().search_count([])
        payload = {
            'simulated': True,
            'action': action_name,
            'requirement_count': requirement_count,
            'draft_requirement_count': draft_requirement_count,
            'requirement_task_count': task_count,
            'run_at': fields.Datetime.now(),
        }
        _logger.info("PMS simulation run: %s", payload)
        return payload

    def action_get_pms_task(self):
        # url = 'http://127.0.0.2:8069'
        # db = 'ODES_PMS_17_MAY'
        # username = 'admin'
        # key = '66cb9897bbb123ff4f7451fd3fc10712af36299e'

        # url = 'https://devteam.odes.com.sg'
        # db = 'ODES_PMS'
        # username = 'admin'
        # key = '0bb41aeca3668925bcb0ef99fd67260f102f9c68'
        if self._is_pms_simulation_enabled():
            return self._simulate_pms_sync('action_get_pms_task')
        rpc_ctx = self._get_pms_rpc_context()
        if not rpc_ctx:
            return False
        param_obj = rpc_ctx['param_obj']
        requirement_obj = self.env['odes.crm.requirement'].sudo()
        draft_requirement_obj = self.env['odes.crm.requirement.draft'].sudo()
        requirement_task_obj = self.env['odes.crm.requirement.task'].sudo()
        db = rpc_ctx['db']
        key = rpc_ctx['key']
        uid = rpc_ctx['uid']
        models = rpc_ctx['models_proxy']
        last_update = param_obj.get_param('odes_crm.pms_last_update') or False
        try:
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
        except Exception as err:
            _logger.warning("PMS sync skipped in action_get_pms_task: %s", err)
            return False

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
        if self._is_pms_simulation_enabled():
            return self._simulate_pms_sync('action_resync_pms_task')
        rpc_ctx = self._get_pms_rpc_context()
        if not rpc_ctx:
            return False
        param_obj = rpc_ctx['param_obj']
        draft_requirement_obj = self.env['odes.crm.requirement.draft'].sudo()
        requirement_obj = self.env['odes.crm.requirement'].sudo()
        db = rpc_ctx['db']
        key = rpc_ctx['key']
        uid = rpc_ctx['uid']
        models = rpc_ctx['models_proxy']
        resync_from = param_obj.get_param('odes_crm.resync_from') or False

        try:
            res_ids = models.execute_kw(db, uid, key, 'project.task', 'search', [[['requirement_number', '!=', False], ['is_sync', '=', True], ['end_date', '>=', resync_from], '|', ['pma_task_id', '=', False], ['pma_task_id', '=', 0]]])
            tasks = models.execute_kw(db, uid, key, 'project.task', 'read', [res_ids], {'fields': ['name', 'module_id', 'requester_id', 'mandays', 'project_id', 'user_id', 'project_team_id', 'date_deadline', 'start_date', 'end_date', 'stage_id', 'requirement_number', 'write_date']})

            for task in tasks:
                requirement = requirement_obj.search([('number', '=', task['requirement_number'])], limit=1)
                # Draft requirement yang sudah confirm bisa ikut tersync ulang
                # saat resync, jadi tetap diproses di dua cabang berikut.
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
        except Exception as err:
            _logger.warning("PMS sync skipped in action_resync_pms_task: %s", err)
            return False

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
