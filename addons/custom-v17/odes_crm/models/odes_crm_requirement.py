# -*- coding: utf-8 -*-
import logging
import re
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from datetime import date, datetime, timedelta


_logger = logging.getLogger(__name__)

class OdesCrmRequirement(models.Model):
    _name = 'odes.crm.requirement'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Requirements'
    _order = 'date desc, id'

    def action_deadline_change_request(self):
        return {
            'name': _('Deadline Change Request'),
            'view_mode': 'form',
            'res_model': 'odes.crm.deadline.change.request.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def action_request_done(self):
        self.ensure_one()
        self.write({
            'is_action_request': False,
            'request_deadline': False,
            'request_responsible_id': False,
        })

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        # name=_("%s (copy)", self.name),
        if self.env.context.get('is_first_moved_requirement'):
            default = dict(default or {},
                        name=self.name,
                        number=self.number,
                        requirement_task_ids=self.requirement_task_ids,
                        event_task_ids=self.event_task_ids,
                        feedback_ids=self.feedback_ids,
                        date=self.date, date_deadline=self.date_deadline, dateSetClient=self.dateSetClient,
                        flow=self.flow, description=self.description,
                        type=self.type, state=self.state,
                        requirement_id=self.id, active=False,
                        is_first_moved_requirement=True
                        )
        else:
            default = dict(default or {},
                        name=self.name,
                        number=self.number,
                        requirement_task_ids=self.requirement_task_ids,
                        event_task_ids=self.event_task_ids,
                        feedback_ids=self.feedback_ids,
                        date=self.date, date_deadline=self.date_deadline, dateSetClient=self.dateSetClient,
                        flow=self.flow, description=self.description,
                        type=self.type, state=self.state,
                        requirement_id=self.id, active=False
                        )

        return super(OdesCrmRequirement, self).copy(default=default)

    @api.model_create_multi
    def create(self, vals_list):
        followers_map = []
        project_obj = self.env['project.project'].sudo()
        partner_obj = self.env['res.partner'].sudo()

        for vals in vals_list:
            if not vals.get('order_id') and not vals.get('project_id'):
                raise UserError(_('You need to have quotation/project before you can create requirement.'))

            partner_ids = []
            project = project_obj.browse(vals.get('project_id'))
            for dev in project.developer_ids:
                if dev and dev.email:
                    partner = partner_obj.search([('email', '=', dev.email), ('company_id', '=', 1)], limit=1)
                    if not partner:
                        new_partner = partner_obj.create({'name': dev.email, 'email': dev.email, 'company_id': 1})
                        partner_ids.append(new_partner)
                    partner_ids.append(partner)
            followers_map.append(set(partner.id for partner in partner_ids if partner))

            if self.env.context.get('from_draft_requirement'):
                vals['number'] = vals['number']
            elif self.env.context.get('from_stage_moved_requirement'):
                vals['number'] = vals['number']
            else:
                vals['number'] = self.env['ir.sequence'].sudo().next_by_code('odes.crm.requirement')

        records = super(OdesCrmRequirement, self).create(vals_list)
        for rec, follower_ids in zip(records, followers_map):
            rec.message_subscribe(list(follower_ids))
        return records

    def write(self, values):
        if self._name == 'odes.crm.requirement.draft':
            res = super(OdesCrmRequirement, self).write(values)
            return res
        # if self.env['odes.crm.requirement.draft'].browse(self.id):
        #     res = super(OdesCrmRequirement, self).write(values)
        #     return res
        if values:
            if not self.is_customer:
                template = self.env.ref('odes_crm.mail_template_odes_crm_requirement_updates', raise_if_not_found=False)
                if template:
                    template.sudo().send_mail(self.id, force_send=True)
        
        if values.get('description'):
            old_value = self.description and self.description.replace("<p>", "<p class='mb-0'>")
            new_value = values.get('description').replace("<p>", "<p class='mb-0'>")
            description_msg = _(
                """
                    <ul class="o_Message_trackingValues">
                        <li>
                            <div class="o_Message_trackingValueFieldName o_Message_trackingValueItem">Description:</div>
                            <div class="o_Message_trackingValue">
                                <div class="o_Message_trackingValueOldValue o_Message_trackingValueItem">%(old_value)s</div>
                                <div title="Changed" role="img" class="o_Message_trackingValueSeparator o_Message_trackingValueItem fa fa-long-arrow-right"></div>
                                <div class="o_Message_trackingValueNewValue o_Message_trackingValueItem">%(new_value)s</div>
                            </div>
                        </li>
                    </li>
                """,
                old_value=old_value, 
                new_value=new_value
            )
            self.message_post(body=description_msg)

        if values.get('flow'):
            old_value = self.flow and self.flow.replace("<p>", "<p class='mb-0'>")
            new_value = values.get('flow').replace("<p>", "<p class='mb-0'>")
            flow_msg = _(
                """
                    <ul class="o_Message_trackingValues">
                        <li>
                            <div class="o_Message_trackingValueFieldName o_Message_trackingValueItem">Flow:</div>
                            <div class="o_Message_trackingValue">
                                <div class="o_Message_trackingValueOldValue o_Message_trackingValueItem">%(old_value)s</div>
                                <div title="Changed" role="img" class="o_Message_trackingValueSeparator o_Message_trackingValueItem fa fa-long-arrow-right"></div>
                                <div class="o_Message_trackingValueNewValue o_Message_trackingValueItem">%(new_value)s</div>
                            </div>
                        </li>
                    </li>
                """,
                old_value=old_value, 
                new_value=new_value
            )
            self.message_post(body=flow_msg)

        if values.get('state_rel'):
            values['state'] = values['state_rel']
            values['state_internal_project_requester'] = values['state_rel']
            if values['state_rel'] not in ['client_confirmed', 'done']:
                values['state_internal_project'] = values['state_rel']
            # values['state'] = values['state_rel']
            # values['state'] = values['state_rel']

        if values.get('state_internal_project'):
            values['state'] = values['state_internal_project']

        if values.get('state_internal_project_requester'):
            values['state'] = values['state_internal_project_requester']

        """ Below is the logic to reset req if it's moved between stages """
        # valid_req = requirement.with_context(ctx).create({
        
        if values.get('stage_id'): #future stage
            if self.is_customer:
                raise ValidationError(_("You are not allowed to move the requirement"))
            else:
                if self.project_type == 'external':
                    requirement_obj = self.env['odes.crm.requirement'].sudo()
                    # We need to check that is the moved req is coming from valid stages
                    if self.stage_id: #previous stage
                        previous_requirement = requirement_obj.search([('requirement_id', '=', self.id), ('stage_id', '=', values.get('stage_id')), ('active', '=', False)])
                        ctx = {'from_stage_moved_requirement': True}
                        if previous_requirement:
                            # previous_requirement.write({'active': True})
                            # self.write({'active': False})
                            duplicated_req = self.with_context(ctx).copy()
                            self.write({
                                'number': previous_requirement.number,
                                'is_main_requirement': True,
                                'date': previous_requirement.date,
                                'date_deadline': previous_requirement.date_deadline,
                                'dateSetClient': previous_requirement.dateSetClient,
                                'description': previous_requirement.description,
                                'flow': previous_requirement.flow,
                                'business_function_id': previous_requirement.business_function_id,
                                'is_action_request': previous_requirement.is_action_request,
                                'request_deadline': previous_requirement.request_deadline,
                                'request_responsible_id': previous_requirement.request_responsible_id,
                                'requirement_status_requester_id': previous_requirement.requirement_status_requester_id,
                                'module_id': previous_requirement.module_id,
                                'type': previous_requirement.type,
                                'priority': previous_requirement.priority,
                                'is_internal_only': previous_requirement.is_internal_only,
                                'is_requirement': previous_requirement.is_requirement,
                                'state': previous_requirement.state,
                                'state_internal_project': previous_requirement.state_internal_project,
                                'state_internal_project_requester': previous_requirement.state_internal_project_requester,
                                'event_task_ids': previous_requirement.event_task_ids,
                                'requirement_task_ids': previous_requirement.requirement_task_ids,
                                'feedback_ids': previous_requirement.feedback_ids,
                            })
                            previous_requirement.unlink()
                            # return {
                            #     'type': 'ir.actions.client',
                            #     'tag': 'reload',
                            # }
                        else:
                            existing_moved_requirement = requirement_obj.search([('requirement_id', '=', self.id), ('active', '=', False)])
                            if not existing_moved_requirement:
                                ctx['is_first_moved_requirement'] = True
                                duplicated_req = self.with_context(ctx).copy()
                            else:
                                # self.write({
                                #     'is_first_moved_requirement': True
                                # })
                                duplicated_req = self.with_context(ctx).copy()

                            # first_previous_moved_requirement = requirement_obj.search([('is_first_moved_requirement', '=', True), ('active', '=', False)], limit=1)
                            
                            # first_previous_moved_requirement = requirement_obj.search([('project_id', '=', self.project_id.id),('is_first_moved_requirement', '=', True), ('active', '=', False)], limit=1)
                            # if first_previous_moved_requirement:
                            #     number = first_previous_moved_requirement.number
                            # else:
                            number = self.number.split('-')[0]
                            if self.req_prefix_number == 0:
                                prefix_number = 1
                            else:
                                prefix_number = self.req_prefix_number
                            self.write({
                                'number': number + "-" + str(prefix_number),
                                'is_main_requirement': True,
                                'date': False,
                                'date_deadline': False,
                                'dateSetClient': False,
                                'description': False,
                                'flow': False,
                                'business_function_id': False,
                                'is_action_request': False,
                                'request_deadline': False,
                                'request_responsible_id': False,
                                'requirement_status_requester_id': False,
                                'module_id': False,
                                'type': False,
                                'priority': False,
                                'is_internal_only': False,
                                'is_requirement': False,
                                'state': 'new',
                                'state_internal_project': 'new',
                                'state_internal_project_requester': 'new',
                            })



        # if self == self.env['odes.crm.requirement.draft'].browse(self.id):
        #     res = super(OdesCrmRequirementDraft, self).write(values)
        #     return res
        # TODO Date Deadline Called when the req is moved to previous one
        res = super(OdesCrmRequirement, self).write(values)
        if values.get('date_deadline'):
            template = self.env.ref('odes_crm.mail_template_odes_crm_deadline_changed', raise_if_not_found=False)
            if template:
                template.sudo().send_mail(self.id, force_send=True)
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, order=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('number', 'ilike', name.split(' ')[0] + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        return self._search(expression.AND([domain, args]), limit=limit, order=order)

    def name_get(self):
        result = []
        for requirement in self:
            name = '[' + requirement.number + '] ' + requirement.name
            result.append((requirement.id, name))
        return result

    def action_client_confirm(self):
        self.ensure_one()
        
        today = datetime.now()
        template = self.env.ref('odes_crm.mail_template_odes_crm_client_confirmed', raise_if_not_found=False)
        if template:
            template.sudo().send_mail(self.id, force_send=True)

        self.write({
            'state': 'client_confirmed',
            'dateSetClient': today,
            'state_internal_project': 'client_confirmed',
            'state_internal_project_requester': 'client_confirmed',
        })

    def action_set_development(self):
        self.ensure_one()
        self.write({
            'state': 'development',
            'state_internal_project': 'development',
            'state_internal_project_requester': 'development',
        })

    def action_done_development(self):
        self.ensure_one()
        id = self.id
        today = date.today()
        # task = self.env['odes.crm.requirement.task'].search([('requirement_id','=',id),('stage','!=','Done')])
        task = self.env['odes.crm.requirement.task'].search([('requirement_id','=',id),('stage','not in', ['Done', 'Cancel', 'Cancelled'])])
        if len(task)>0:
            raise UserError(_("There are still some developer tasks that haven't been done yet"))
        template = self.env.ref('odes_crm.mail_template_odes_crm_development_done', raise_if_not_found=False)
        if template:
            template.sudo().send_mail(self.id, force_send=True)

        self.write({
            'state': 'done_development',
            'state_internal_project': 'done_development',
            'state_internal_project_requester': 'done_development',
            'date_pm_confirm': today
        })

    def action_prompt_client_confirmed_followup(self):
        self.ensure_one()

        template = self.env.ref('odes_crm.mail_template_odes_crm_client_confirmed_followup', raise_if_not_found=False)
        if template:
            template.sudo().send_mail(self.id, force_send=True)

    def action_pm_confrm(self):
        self.ensure_one()
        self.write({
            'state': 'pm_confirmed',
            'state_internal_project': 'pm_confirmed',
            'state_internal_project_requester': 'pm_confirmed',
        })

    def action_done(self):
        self.ensure_one()
        self.write({
            'state': 'done',
            'state_internal_project_requester': 'done',
        })

        template = self.env.ref('odes_crm.mail_template_odes_crm_client_confirmed_done', raise_if_not_found=False)
        if template:
            template.sudo().send_mail(self.id, force_send=True)

    def action_notify_client(self):
        partner_ids = []
        context = self.env.context.copy()
        context.update({'requirements': self, 'state': dict(self._fields['state'].selection)})
        requirement = self.browse(self._ids[0])
        emails = [partner.email for partner in requirement.partner_ids]

        try:
            template = self.env.ref('odes_crm.mail_template_odes_crm_notify_client')
            body_html = template.with_context(context)._render_template(
                template.body_html,
                'odes.crm.requirement',
                [requirement.id],
            ).get(requirement.id)
            subject = template.with_context(context).subject
            mail_server = self.env['ir.mail_server']
            message = mail_server.build_email(
                email_from='%s <%s>' % (requirement.company_id.name, (requirement.company_id.email or self.env.user.email)),
                subject=subject,
                body=body_html,
                subtype='html',
                email_to=emails,
            )
            mail_server.send_email(message)
        except Exception as e:
            _logger.error("Error occurred, please contact your technical support. Error message: {}".format(e))
    

    def action_set_manhours(self):
        requirement_obj = self.env['odes.crm.requirement'].sudo()
        requirements = requirement_obj.search([])
        # requirements = requirement_obj.browse(self.id)
        # Search []

        for requirement in requirements:
            for event in requirement.event_task_ids:
                if event.manhours2 == False:
                    event.manhours2 = event.manhours


    def action_new_feedback(self):
        self.ensure_one()
        context = self.env.context.copy()
        context['default_requirement_id'] = self.id
        view_id = self.env['ir.model.data'].xmlid_to_res_id('odes_crm.view_odes_crm_requirement_feedback_popup_form')
        return {
            'name': _('New Feedback'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'odes.crm.requirement.feedback',
            'views': [[view_id, 'form']],
            'target': 'new',
            'context': context
        }

    def get_pm_email(self):
        self.ensure_one()
        if self.order_id and self.order_id.pm_user_id:
            return self.order_id.pm_user_id.email

        if self.project_id and self.project_id.user_id:
            return self.project_id.user_id.email

        return False

    def get_dev_email(self):
        self.ensure_one()
        dev = []
        if self.project_id:
            for user in self.project_id.developer_ids:
                dev.append(user.email)
        developer = ''
        for ele in dev:
            developer += ele + ', '
        return developer[:-2]

    def get_pic_email(self):
        self.ensure_one()
        pic = []
        for req in self:
            if req.internal_user_ids:
                for user in req.internal_user_ids:
                    if user.email:
                        pic.append(user.email)
        if self.project_id:
            for user in self.project_id.user_id:
                if user.email and (user.email != 'soohian@mccoy.com.sg' and user.email != 'ifran@mccoy.com.sg'):
                    pic.append(user.email)
        person_in_charge = ''
        for ele in pic:
            person_in_charge += ele + ', '
        return person_in_charge[:-2]

    def get_deadline_notify_email(self):
        self.ensure_one()
        pic = []
        for req in self:
            if req.internal_user_ids:
                for user in req.internal_user_ids:
                    pic.append(user.email)
        if self.project_id:
            for user in self.project_id.user_id:
                pic.append(user.email)
            for user in self.project_id.developer_ids:
                pic.append(user.email)
        
        person_in_charge = ''
        for ele in pic:
            if ele:
                person_in_charge += ele + ', '
        return person_in_charge[:-2]

    def get_reporting_group_email(self):
        self.ensure_one()
        reporting = int(self.env.ref('odes_crm.group_odes_reporting_officer'))
        users = self.env['res.users'].sudo().search([('groups_id', '=', reporting)])
        email = [user.login for user in users if user.login]
        data = ', '.join(email)

        return data

    def action_reminder_requirement_deadline(self):
        today = date.today()
        requirements = self.env['odes.crm.requirement'].search([
            ('state', 'not in', ['pm_confirmed', 'done']),
            ('date_deadline', '!=', False),
            ('is_sent_deadline_exceeded_reminder', '=', False),
        ])
        for req in requirements:
            if req.date_deadline:
                """ Indicates 48 Hours & 24 Hours before Deadline and also deadline exceeded """
                two_days_before_deadline = req.date_deadline - timedelta(days=2)
                one_days_before_deadline = req.date_deadline - timedelta(days=1)

                if two_days_before_deadline == today:
                    template = self.env.ref('odes_crm.mail_template_odes_crm_reminder_pic_48_hours', raise_if_not_found=False)
                    if template:
                        template.sudo().send_mail(req.id, force_send=True)
                elif one_days_before_deadline == today:
                    template = self.env.ref('odes_crm.mail_template_odes_crm_reminder_pic_24_hours', raise_if_not_found=False)
                    if template:
                        template.sudo().send_mail(req.id, force_send=True)
                elif req.date_deadline < today:
                    template = self.env.ref('odes_crm.mail_template_odes_crm_warning_exceeded_deadline_requirement', raise_if_not_found=False)
                    if template:
                        template.sudo().send_mail(req.id, force_send=True)
                        req.write({
                            'is_sent_deadline_exceeded_reminder': True
                        })
                # if int(req.date_deadline.strftime('%d')) - int(today.strftime('%d')) == 2:
                #     template = self.env.ref('odes_crm.mail_template_odes_crm_reminder_pic_48_hours', raise_if_not_found=False)
                #     if template:
                #         template.sudo().send_mail(req.id, force_send=True)
                # elif int(req.date_deadline.strftime('%d')) - int(today.strftime('%d')) == 1:
                #     template = self.env.ref('odes_crm.mail_template_odes_crm_reminder_pic_24_hours', raise_if_not_found=False)
                #     if template:
                #         template.sudo().send_mail(req.id, force_send=True)
                # elif req.date_deadline < today:
                #     template = self.env.ref('odes_crm.mail_template_odes_crm_warning_exceeded_deadline_requirement', raise_if_not_found=False)
                #     if template:
                #         template.sudo().send_mail(req.id, force_send=True)
                #         req.write({
                #             'is_sent_deadline_exceeded_reminder': True
                #         })

    def cron_after_send_client_confirm(self):
        template = self.env.ref('odes_crm.mail_template_odes_crm_client_confirmed', raise_if_not_found=False)
        time_cc = self.env['odes.crm.requirement'].search([('state', '=', 'client_confirmed')])
        current_time = datetime.now()
        for id in time_cc:
            if not id.dateSetClient:
                continue
            sumDateNow = id.dateSetClient + timedelta(days=1, hours=8)
            if current_time > sumDateNow:
                if template:
                    template.sudo().send_mail(id.id, force_send=True)
    # belum selesai
    def cron_send_pm_confirm(self):
        template = self.env.ref('odes_crm.mail_template_odes_crm_reminder_pm', raise_if_not_found=False)
        time_cc = self.env['odes.crm.requirement'].search([('state', '=', 'done_development')])
        current_time = date.today()
        for id in time_cc:
            if id.date_pm_confirm:
                sumDateNow = current_time - id.date_pm_confirm
                countTIme = int(sumDateNow.days)
                if countTIme > 1 :
                    if template:
                        template.sudo().send_mail(id.id, force_send=True)
                        id.write({'date_pm_confirm': current_time})

    @api.model
    def _default_order_id(self):
        context = self.env.context
        order_obj = self.env['sale.order'].sudo()

        if context.get('default_order_id'):
            return context['default_order_id']
        else:
            order = order_obj.search([('partner_id', '=', self.env.user.partner_id.id)], limit=1)
            if order:
                return order.id

        return order_obj

    @api.model
    def _default_project_id(self):
        context = self.env.context
        project_obj = self.env['project.project'].sudo()

        if context.get('default_project_id'):
            return context['default_project_id']
        else:
            project = project_obj.sudo().search([('customer_user_ids', 'in', [self.env.user.id])], limit=1)
            if project:
                return project.id

        return project_obj

    def _default_internal_user_ids(self):
        context = self.env.context

        if context.get('default_internal_member_ids'):
            return context['default_internal_member_ids']
        else:
            return []

    def _compute_partner_ids(self):
        for requirement in self:
            partner_ids = []
            if requirement.order_id:
                partner_ids.append(requirement.order_id.partner_id.id)
            if requirement.project_id and requirement.project_id.customer_user_ids:
                for user in requirement.project_id.customer_user_ids:
                    if user.partner_id.id not in partner_ids:
                        partner_ids.append(user.partner_id.id)
            if requirement.project_id and requirement.project_id.allowed_portal_user_ids:
                for user in requirement.project_id.allowed_portal_user_ids:
                    if user.partner_id.id not in partner_ids:
                        partner_ids.append(user.partner_id.id)

            requirement.partner_ids = [(6, 0, partner_ids)]

    def _compute_requirement_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        second_url = '/web#id='
        third_url = '&view_type=form&model=odes.crm.requirement&action='
        action = self.env['ir.actions.actions']._for_xml_id('odes_crm.action_odes_crm_my_requirement')

        for requirement in self:
            full_url = base_url+second_url+str(requirement.id)+third_url+str(action['id'])
            requirement.requirement_url = full_url

    def _compute_company_id(self):
        for requirement in self:
            company_id = False
            if requirement.order_id:
                company_id = requirement.order_id.company_id.id
            elif requirement.project_id:
                company_id = requirement.project_id.company_id.id

            requirement.company_id = company_id

    @api.depends('feedback_ids', 'feedback_ids.state')
    def _compute_is_pending_feedback(self):
        for requirement in self:
            draft_feedback = requirement.feedback_ids.filtered(lambda feedback: feedback.state == 'draft')
            requirement.is_pending_feedback = draft_feedback and True or False

    @api.depends('requirement_task_ids', 'requirement_task_ids.mandays')
    def _compute_consumed_mandays(self):
        valid_status = self.env['ir.config_parameter'].get_param('odes_crm.valid_status').split(', ')
        for requirement in self:
            mandays = 0.00
            for task in requirement.requirement_task_ids:
                if task.stage in valid_status:
                    mandays += task.mandays
            requirement.consumed_mandays = mandays
            # requirement.consumed_mandays = sum(task.mandays for task in requirement.requirement_task_ids if task.stage in [valid_status])

    @api.depends('estimated_mandays', 'consumed_mandays')
    def _compute_outstanding_mandays(self):
        for requirement in self:
            requirement.outstanding_mandays = requirement.estimated_mandays - requirement.consumed_mandays

    @api.depends('event_task_ids', 'event_task_ids.manhours2')
    def _compute_total_manhours(self):
        for requirement in self:
            requirement.total_manhours = sum(event.manhours2 / 8 for event in requirement.event_task_ids)
            # total = 0
            # for line in requirement.event_task_ids:
            #     total += line.manhours2 / 8
            # requirement.total_manhours = total

    """ Will be used in server action once after updating to get old values """
    def _compute_status(self):
        for requirement in self:
            if requirement.state:
                requirement.state_internal_project = requirement.state
                requirement.state_internal_project_requester = requirement.state

    @api.depends('req_prefix_number')
    def _compute_req_prefix_number(self):
        for req in self:
            if req.is_main_requirement:
                child_req = self.env['odes.crm.requirement'].search_count([('requirement_id', '=', req.id), ('active', '=', False)])
                req.req_prefix_number = child_req
            else:
                req.req_prefix_number = False

    def _compute_is_customer(self):
        customer = self.env.ref('odes_crm.group_odes_customer').sudo().users.ids
        ctx = self._context or {}
        uid = ctx.get('uid')
        self.is_customer = uid in customer

    def _read_group_stage_ids(self,stages,domain,order):
        search_domain = [('id', 'in', stages.ids)]
        if 'default_project_id' in self.env.context:
            search_domain = ['|', ('project_ids', '=', self.env.context['default_project_id'])] + search_domain

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.depends('requirement_task_ids')
    def _compute_uncompleted_task(self):
        for requirement in self:
            count = 0
            for task in requirement.requirement_task_ids:
                # if task.stage not in ['Done', 'Cancel']:
                if task.stage != 'Done':
                    count += 1
            requirement.uncompleted_task = count

    # To be used in server action for the first time computation
    def _compute_server_uncompleted_task(self):
        requirements = self.env['odes.crm.requirement'].sudo().search([])
        for requirement in requirements:
            count = 0
            for task in requirement.requirement_task_ids:
                # if task.stage not in ['Done', 'Cancel']:
                if task.stage != 'Done':
                    count += 1
            requirement.uncompleted_task = count

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Title', tracking=True)
    number = fields.Char('Number', tracking=True)
    date = fields.Date('Date', default=fields.Date.context_today, tracking=True)
    date_pm_confirm = fields.Date('Date om Confirm',tracking=True)
    dateSetClient = fields.Date('Client Confirmed Date', tracking=True)
    date_deadline = fields.Date('Deadline', tracking=True)
    module_id = fields.Many2one('odes.crm.requirement.module', string='Apps', tracking=True)
    type = fields.Selection([
        ('custom', 'Customization'), 
        ('semi', 'Semi-Customization'), 
        ('setup', 'Setup'),
        ('variation', 'Variation Order')], string='Type', tracking=True)
    description = fields.Text('Description')
    state_internal_project = fields.Selection([
        ('new', 'New'), 
        ('client_confirmed', 'Confirmed by Client'), 
        ('development', 'On Development'), 
        ('done_development', 'Done Development'), 
        ('pm_confirmed', 'Confirmed by PM')], default='new', string='Internal Project Status')
    state_internal_project_requester = fields.Selection([
        ('new', 'New'), 
        ('client_confirmed', 'Confirmed by Client'), 
        ('development', 'On Development'), 
        ('done_development', 'Done Development'), 
        ('pm_confirmed', 'Confirmed by PM'), 
        ('done', 'Confirmed by Client (Done)')], default='new', string='Requester Status')
    state = fields.Selection([
        ('new', 'New'), 
        ('client_confirmed', 'Confirmed by Client'), 
        ('development', 'On Development'), 
        ('done_development', 'Done Development'), 
        ('pm_confirmed', 'Confirmed by PM'), 
        ('done', 'Confirmed by Client (Done)')], default='new', string='Workflow Status', tracking=True)
    state_rel = fields.Selection(related='state', string='Status (Readonly)')
    attachment_ids = fields.Many2many('ir.attachment', 'odes_crm_requirement_attachment_ids', 'requirement_id', 'attachment_id', string='Attachments')
    feedback_ids = fields.One2many('odes.crm.requirement.feedback', 'requirement_id', string='Feedback')
    flow = fields.Text('Flow')
    priority = fields.Selection([('mandatory', 'Mandatory'), ('good_to_have', 'Good to Have'), ('bugs', 'Bugs/Issues')], string='Priority')
    business_function_id = fields.Many2one('odes.crm.business.function', string='Business Function', tracking=True)
    internal_user_ids = fields.Many2many('res.users', 'odes_crm_requirement_res_users_rel', 'requirement_id', 'user_id', default=_default_internal_user_ids, string='Internal Members')
    requirement_task_ids = fields.One2many('odes.crm.requirement.task', 'requirement_id', string='Tasks')
    order_id = fields.Many2one('sale.order', default=_default_order_id, string='Order Reference', tracking=True)
    project_id = fields.Many2one('project.project', default=_default_project_id, string='Project', tracking=True)
    partner_ids = fields.Many2many('res.partner', 'odes_crm_requirement_res_partner_rel', 'requirement_id', 'partner_id', compute='_compute_partner_ids', string='Related Customers')
    requirement_url = fields.Char(compute='_compute_requirement_url', string='Requirement Url')
    company_id = fields.Many2one('res.company', compute='_compute_company_id', string='Company')
    is_pending_feedback = fields.Boolean(compute='_compute_is_pending_feedback', string='Pending Feedback', store=True)
    event_task_ids = fields.One2many('calendar.event', 'requirement_id', string='Calendar Tasks')
    estimated_mandays = fields.Float('Estimated Mandays', digits=(16,3), tracking=True)
    consumed_mandays = fields.Float(compute='_compute_consumed_mandays', string='Completed Mandays', digits=(16,3), store=True)
    outstanding_mandays = fields.Float(compute='_compute_outstanding_mandays', string='Outstanding Mandays', digits=(16,3), store=True)
    total_manhours = fields.Float(compute='_compute_total_manhours', string='Total Tasks Mandays', digits=(16,3), store=True)
    pm_estimated_mandays = fields.Float('PM Estimated Mandays', digits=(16,3), tracking=True)
    is_action_request = fields.Boolean(string='Action Request')
    request_deadline = fields.Date('Request Deadline', tracking=True)
    request_responsible_id = fields.Many2one(comodel_name='res.users', string='Request Responsible', tracking=True)
    is_sent_deadline_exceeded_reminder = fields.Boolean(string='Is Sent Deadline Exceeded Reminder')
    stage_id = fields.Many2one('odes.crm.requirement.type', string='Stage', group_expand='_read_group_stage_ids', tracking=True)
    # project_ids = fields.Many2many('project.project', 'project_requirement_type_rel', 'type_id', 'project_id', string='Projects',
    #     )
    # project_ids = fields.Many2one(string="Stage",comodel_name='odes.crm.requirement.type')
    requirement_status_requester_id = fields.Many2one(comodel_name='res.users', string='Requester')
    project_type = fields.Selection(related="project_id.project_type", string='Project Type')
    project_name = fields.Char(related="project_id.name", string='Project Name')
    is_internal_only = fields.Boolean(string='Internal Only')
    is_requirement = fields.Boolean(string='Task Not Required')
    requirement_id = fields.Many2one(comodel_name='odes.crm.requirement', string='Requirement From')
    is_main_requirement = fields.Boolean(string='Is Main Requirement', copy=False)
    # prefix_number = fields.Integer('Prefix Number', default=1)
    req_prefix_number = fields.Integer(compute='_compute_req_prefix_number', string='Requirement Prefix Number')
    is_first_moved_requirement = fields.Boolean(string='First Moved Requirement', copy=False)
    is_customer = fields.Boolean(compute='_compute_is_customer', string='Is Customer')
    uncompleted_task = fields.Integer(compute='_compute_uncompleted_task', string='Uncompleted Task', store=True)

class OdesCrmRequirementModule(models.Model):
    _name = 'odes.crm.requirement.module'
    _description = 'Requirement Modules'

    name = fields.Char('Name')

class OdesCrmRequirementFeedback(models.Model):
    _name = 'odes.crm.requirement.feedback'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Requirement Feedback'

    def write(self, values):
        if values.get('description'):
            old_value = self.description and self.description.replace("<p>", "<p class='mb-0'>")
            new_value = values.get('description').replace("<p>", "<p class='mb-0'>")
            description_msg = _(
                """
                    <ul class="o_Message_trackingValues">
                        <li>
                            <div class="o_Message_trackingValueFieldName o_Message_trackingValueItem">Description:</div>
                            <div class="o_Message_trackingValue">
                                <div class="o_Message_trackingValueOldValue o_Message_trackingValueItem">%(old_value)s</div>
                                <div title="Changed" role="img" class="o_Message_trackingValueSeparator o_Message_trackingValueItem fa fa-long-arrow-right"></div>
                                <div class="o_Message_trackingValueNewValue o_Message_trackingValueItem">%(new_value)s</div>
                            </div>
                        </li>
                    </li>
                """,
                old_value=old_value, 
                new_value=new_value
            )
            self.message_post(body=description_msg)

        res = super(OdesCrmRequirementFeedback, self).write(values)
        return res

    def unlink(self):
        for feedback in self:
            if feedback.state != 'draft':
                raise UserError(_('You can only delete draft feedback.'))

        return super(OdesCrmRequirementFeedback, self).unlink()

    def action_draft(self):
        self.ensure_one()
        self.write({
            'state': 'draft'    
        })

    def action_approve(self):
        self.ensure_one()
        self.write({
            'state': 'approved' 
        })

    def action_done(self):
        self.ensure_one()
        self.write({
            'state': 'done' 
        })

    def action_reject(self):
        self.ensure_one()
        self.write({
            'state': 'rejected' 
        })

    def action_prompt_to_developer(self):
        # this function for  send email to client
        template = self.env.ref('odes_crm.mail_template_odes_crm_feedback_dev', raise_if_not_found=False)
        if template:
            email = template.sudo().send_mail(self.id, force_send=True)
            if email:
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': ('Successfully Sent'),
                        'message': 'Your feedback message has been successfully sent to the Project Developer',
                        'type':'success',  #types: success,warning,danger,info
                        'sticky': False,  #True/False will display for few seconds if false
                    },
                }
                return notification

    def action_prompt_to_pm(self):
        # this function for send email to pm
        template = self.env.ref('odes_crm.mail_template_odes_crm_feedback_pm', raise_if_not_found=False)
        if template:
            email = template.sudo().send_mail(self.id, force_send=True)
            if email:
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': ('Successfully Sent'),
                        'message': 'Your feedback message has been successfuly sent to the Project Manager',
                        'type':'success',  #types: success,warning,danger,info
                        'sticky': False,  #True/False will display for few seconds if false
                    },
                }
                return notification

    def action_edit_feedback(self):
        self.ensure_one()
        context = self.env.context.copy()
        view_id = self.env['ir.model.data'].xmlid_to_res_id('odes_crm.view_odes_crm_requirement_feedback_popup_form')
        return {
            'name': _('Edit Feedback'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'odes.crm.requirement.feedback',
            'res_id': self.id,
            'views': [[view_id, 'form']],
            'target': 'new',
            'context': context
        }

    name = fields.Char('Feedback', tracking=True)
    description = fields.Text('Description')
    date = fields.Date('Date', default=fields.Date.context_today, tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('rejected', 'Rejected'), ('approved', 'Approved'), ('done', 'Done'), ('transferred', 'Transferred to New Requirement')], default='draft', string='Status', tracking=True)
    transferred_requirement_id = fields.Many2one('odes.crm.requirement', string='Transferred Requirement', tracking=True)
    requirement_id = fields.Many2one('odes.crm.requirement', string='Requirement', tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', 'odes_crm_requirement_feedback_attachment_ids', 'feedback_id', 'attachment_id', string='Attachments')

class OdesCrmRequirementTask(models.Model):
    _name = 'odes.crm.requirement.task'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Requirement Tasks'

    name = fields.Char('Name', tracking=True)
    module = fields.Char('Module', tracking=True)
    requester = fields.Char('Requester', tracking=True)
    mandays = fields.Float('Mandays', digits=(16,3), tracking=True)
    project = fields.Char('Project', tracking=True)
    user = fields.Char('Assigned to', tracking=True)
    team = fields.Char('Team', tracking=True)
    date_deadline = fields.Date('Deadline', tracking=True)
    start_date = fields.Date('Start Date', tracking=True)
    end_date = fields.Date('End Date', tracking=True)
    stage = fields.Char('Stage', tracking=True)
    requirement_id = fields.Many2one('odes.crm.requirement', string='Requirement', tracking=True)
    draft_requirement_id = fields.Many2one('odes.crm.requirement.draft', string='Draft Requirement', tracking=True)
    pms_task_id = fields.Integer('PMS Task ID', tracking=True)

    def action_generate_mandays_report(self):
        return {
            'name': _('Mandays Report'),
            'view_mode': 'form',
            'res_model': 'mandays.monthly.report.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

class OdesCrmRequirementDevelopers(models.Model):
    _name = 'odes.crm.requirement.developers'
    _description = 'Odes Developers'

    name = fields.Char('Name')
    email = fields.Char(string='Email')

class OdesCrmRequirementType(models.Model):
    _name = 'odes.crm.requirement.type'
    _description = 'Odes Type'
    _order = 'sequence, id'

    def _get_default_project_type_ids(self):
        default_project_id = self.env.context.get('default_project_id')
        return [default_project_id] if default_project_id else None

    @api.depends('project_ids', 'project_ids.rating_active')
    def _compute_disabled_rating_warning(self):
        for stage in self:
            disabled_projects = stage.project_ids.filtered(lambda p: not p.rating_active)
            if disabled_projects:
                stage.disabled_rating_warning = '\n'.join('- %s' % p.name for p in disabled_projects)
            else:
                stage.disabled_rating_warning = False

    def lock_stage(self):
        project_stage_status_obj = self.env['odes.crm.requirement.type.status'].sudo()

        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].sudo().browse(project_id)
        # project_stage_status = project_stage_status_obj.search([('project_id', '=', project.id), ('stage_id', '=' self.id)])
        project_stage_status = project_stage_status_obj.search([('project_id', '=', project.id), ('stage_id', '=', self.id)])
        if not project_stage_status:
            new_project_status = project_stage_status_obj.create({
                'name': project.name + ' ' + self.name,
                'project_id': project.id,
                'stage_id': self.id,
                'is_locked': True
            })
            self.write({
                'stage_status_id': new_project_status.id
            })
        else:
            project_stage_status.write({
                'is_locked': True
            })
            self.write({
                'stage_status_id': project_stage_status.id
            })

    def unlock_stage(self):
        project_stage_status_obj = self.env['odes.crm.requirement.type.status'].sudo()
        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].sudo().browse(project_id)
        project_stage_status = project_stage_status_obj.search([('project_id', '=', project.id), ('stage_id', '=', self.id), ('is_locked', '=', True)])
        if project_stage_status:
            project_stage_status.write({
                'is_locked': False
            })

    @api.depends('is_locked')
    def _compute_is_locked(self):
        project_stage_status_obj = self.env['odes.crm.requirement.type.status'].sudo()
        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].sudo().browse(project_id)
        for stage in self:
            project_stage_status = project_stage_status_obj.search([('project_id', '=', project.id), ('stage_id', '=', stage.id), ('is_locked', '=', True)])
            if project_stage_status: 
                stage.is_locked = True
            else:
                stage.is_locked = False

    def _inverse_is_locked(self):
        project_stage_status_obj = self.env['odes.crm.requirement.type.status'].sudo()
        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].sudo().browse(project_id)
        for rec in self:
            project_stage_status = project_stage_status_obj.search([('project_id', '=', project.id), ('stage_id', '=', rec.id)])
            if not project_stage_status: 
                new_project_status = project_stage_status_obj.create({
                    'name': project.name + ' ' + self.name,
                    'project_id': project.id,
                    'stage_id': self.id,
                    'is_locked': True
                })
                self.write({
                    'stage_status_id': new_project_status.id
                })
            else:
                if project_stage_status.is_locked: 
                    project_stage_status.is_locked = False
                else:
                    project_stage_status.is_locked = True

    @api.depends('start_date')
    def _compute_start_date(self):
        project_stage_status_obj = self.env['odes.crm.requirement.type.status'].sudo()
        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].sudo().browse(project_id)
        for stage in self:
            project_stage_status = project_stage_status_obj.search([('project_id', '=', project.id), ('stage_id', '=', stage.id)])
            if project_stage_status: 
                stage.start_date = project_stage_status.start_date
            else:
                stage.start_date = False

    def _inverse_start_date(self):
        project_stage_status_obj = self.env['odes.crm.requirement.type.status'].sudo()
        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].sudo().browse(project_id)
        for rec in self:
            project_stage_status = project_stage_status_obj.search([('project_id', '=', project.id), ('stage_id', '=', rec.id)])
            if not project_stage_status: 
                new_project_status = project_stage_status_obj.create({
                    'name': project.name + ' ' + self.name,
                    'project_id': project.id,
                    'stage_id': self.id,
                    'start_date': self.start_date,
                })
                self.write({
                    'stage_status_id': new_project_status.id
                })
            else:
                if project_stage_status.start_date: 
                    project_stage_status.start_date = self.start_date
                else:
                    project_stage_status.start_date = self.start_date

    @api.depends('end_date')
    def _compute_end_date(self):
        project_stage_status_obj = self.env['odes.crm.requirement.type.status'].sudo()
        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].sudo().browse(project_id)
        for stage in self:
            project_stage_status = project_stage_status_obj.search([('project_id', '=', project.id), ('stage_id', '=', stage.id)])
            if project_stage_status: 
                stage.end_date = project_stage_status.end_date
            else:
                stage.end_date = False

    def _inverse_end_date(self):
        project_stage_status_obj = self.env['odes.crm.requirement.type.status'].sudo()
        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].sudo().browse(project_id)
        for rec in self:
            project_stage_status = project_stage_status_obj.search([('project_id', '=', project.id), ('stage_id', '=', rec.id)])
            if not project_stage_status: 
                new_project_status = project_stage_status_obj.create({
                    'name': project.name + ' ' + self.name,
                    'project_id': project.id,
                    'stage_id': self.id,
                    'end_date': self.end_date,
                })
                self.write({
                    'stage_status_id': new_project_status.id
                })
            else:
                if project_stage_status.end_date: 
                    project_stage_status.end_date = self.end_date
                else:
                    project_stage_status.end_date = self.end_date

    @api.depends('deadline')
    def _compute_deadline(self):
        project_stage_status_obj = self.env['odes.crm.requirement.type.status'].sudo()
        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].sudo().browse(project_id)
        for stage in self:
            project_stage_status = project_stage_status_obj.search([('project_id', '=', project.id), ('stage_id', '=', stage.id)])
            if project_stage_status: 
                stage.deadline = project_stage_status.deadline
            else:
                stage.deadline = False

    def _inverse_deadline(self):
        project_stage_status_obj = self.env['odes.crm.requirement.type.status'].sudo()
        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].sudo().browse(project_id)
        for rec in self:
            project_stage_status = project_stage_status_obj.search([('project_id', '=', project.id), ('stage_id', '=', rec.id)])
            if not project_stage_status: 
                new_project_status = project_stage_status_obj.create({
                    'name': project.name + ' ' + self.name,
                    'project_id': project.id,
                    'stage_id': self.id,
                    'deadline': self.deadline,
                })
                self.write({
                    'stage_status_id': new_project_status.id
                })
            else:
                if project_stage_status.deadline:
                    project_stage_status.deadline = self.deadline
                else:
                    project_stage_status.deadline = self.deadline

    @api.depends('stage_status_ids')
    def _compute_stage_status_ids(self):
        project_stage_status_obj = self.env['odes.crm.requirement.type.status'].sudo()
        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].sudo().browse(project_id)
        project_stage_status = project_stage_status_obj.search([('project_id', '=', project.id), ('stage_id', '=', self.id)])
        for stage in self:
            if project_stage_status:
                stage.stage_status_ids = project_stage_status
            else:
                stage.stage_status_ids = False

    @api.depends('stage_status_id')
    def _compute_stage_status_id(self):
        project_stage_status_obj = self.env['odes.crm.requirement.type.status'].sudo()
        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].sudo().browse(project_id)
        project_stage_status = project_stage_status_obj.search([('project_id', '=', project.id), ('stage_id', '=', self.id)])
        for stage in self:
            if project_stage_status:
                stage.stage_status_id = project_stage_status
            else:
                stage.stage_status_id = False

    @api.depends('project_id')
    def _compute_project_id(self):
        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].sudo().browse(project_id)
        for stage in self:
            if project:
                stage.project_id = project.id
            else:
                stage.project_id = False

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_ids = fields.Many2many('project.project', 'odes_crm_requirement_type_rel', 'type_id', 'project_id', string='Projects',
        default=_get_default_project_type_ids)
    
    legend_blocked = fields.Char(
        'Red Kanban Label', default=lambda s: _('Blocked'), translate=True, required=True,
        help='Override the default value displayed for the blocked state for kanban selection, when the task or issue is in that stage.')
    legend_done = fields.Char(
        'Green Kanban Label', default=lambda s: _('Ready'), translate=True, required=True,
        help='Override the default value displayed for the done state for kanban selection, when the task or issue is in that stage.')
    legend_normal = fields.Char(
        'Grey Kanban Label', default=lambda s: _('In Progress'), translate=True, required=True,
        help='Override the default value displayed for the normal state for kanban selection, when the task or issue is in that stage.')
    mail_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'project.task')],
        help="If set an email will be sent to the customer when the task or issue reaches this step.")
    fold = fields.Boolean(string='Folded in Kanban',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')
    rating_template_id = fields.Many2one(
        'mail.template',
        string='Rating Email Template',
        domain=[('model', '=', 'project.task')],
        help="If set and if the project's rating configuration is 'Rating when changing stage', then an email will be sent to the customer when the task reaches this step.")
    auto_validation_kanban_state = fields.Boolean('Automatic kanban status', default=False,
        help="Automatically modify the kanban state when the customer replies to the feedback for this stage.\n"
            " * A good feedback from the customer will update the kanban state to 'ready for the new stage' (green bullet).\n"
            " * A medium or a bad feedback will set the kanban state to 'blocked' (red bullet).\n")
    is_closed = fields.Boolean('Closing Stage', help="Tasks in this stage are considered as closed.")
    disabled_rating_warning = fields.Text(compute='_compute_disabled_rating_warning')
    # stage_status_id = fields.Many2one(comodel_name='odes.crm.requirement.type.status', string='Status Id')
    project_id = fields.Many2one(comodel_name='project.project', string='Project', compute='_compute_project_id')
    # stage_status_ids = fields.One2many(comodel_name='odes.crm.requirement.type.status', inverse_name='stage_id', domain="[('project_id', '=', 13)]", string='Project Stage Status')
    stage_status_id = fields.Many2one(comodel_name='odes.crm.requirement.type.status', compute='_compute_stage_status_id', string='Project Stage Status')
    # is_locked = fields.Boolean(string='Is Locked', related="stage_status_id.is_locked")
    is_locked = fields.Boolean(compute='_compute_is_locked', inverse="_inverse_is_locked", string='Is Locked')
    start_date = fields.Date(compute='_compute_start_date', inverse="_inverse_start_date", string='Start Date')
    end_date = fields.Date(compute='_compute_end_date', inverse="_inverse_end_date", string='End Date')
    deadline = fields.Date(compute='_compute_deadline', inverse="_inverse_deadline", string='Deadline')

class OdesCrmRequirementTypeStatus(models.Model):
    _name = 'odes.crm.requirement.type.status'
    _description = 'Odes Type Status'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    project_id = fields.Many2one(comodel_name='project.project', string='Project')
    stage_id = fields.Many2one(comodel_name='odes.crm.requirement.type', string='Stage')
    is_locked = fields.Boolean(string='Is Locked Stage')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    deadline = fields.Date(string='Deadline')

class OdesCrmRequirementDraft(models.Model):
    _name = 'odes.crm.requirement.draft'
    _inherit = 'odes.crm.requirement'
    _description = 'Draft Requirements'

    def _default_internal_user_ids(self):
        context = self.env.context

        if context.get('default_internal_member_ids'):
            return context['default_internal_member_ids']
        else:
            return []

    def write(self,values):
        res = super(OdesCrmRequirementDraft, self).write(values)
        return res

    def action_pm_confirm_draft(self):
        self.ensure_one()
        self.write({
            'draft_req_state': 'confirmed',
        })
        requirement = self.env['odes.crm.requirement'].sudo()
        ctx = {'from_draft_requirement': True}
        valid_req = requirement.with_context(ctx).create({
            'number': self.number,
            'name': self.name,
            'date': self.date,
            'date_deadline': self.date_deadline,
            'module_id': self.module_id.id,
            'type': self.type,
            'description': self.description,
            'flow': self.flow,
            'stage_id': self.stage_id.id,
            'internal_user_ids': self.internal_user_ids.ids,
            'order_id': self.order_id.id,
            'project_id': self.project_id.id,
            'partner_ids': self.partner_ids.ids,
            'estimated_mandays': self.estimated_mandays,
            'pm_estimated_mandays': self.pm_estimated_mandays,
            'priority': self.priority,
            'business_function_id': self.business_function_id.id,
            'attachment_ids': self.attachment_ids.ids,
            'requirement_task_ids': self.requirement_task_ids.ids
        })

    active = fields.Boolean('Active', default=True)
    attachment_ids = fields.Many2many('ir.attachment', 'odes_crm_requirement_draft_attachment_ids', 'requirement_id', 'attachment_id', string='Attachments')
    internal_user_ids = fields.Many2many('res.users', 'odes_crm_requirement_draft_res_users_rel', 'requirement_id', 'user_id', default=_default_internal_user_ids, string='Internal Members')
    partner_ids = fields.Many2many('res.partner', 'odes_crm_requirement_draft_res_partner_rel', 'requirement_id', 'partner_id', compute='_compute_partner_ids', string='Related Customers')
    requirement_task_ids = fields.One2many('odes.crm.requirement.task', 'draft_requirement_id', string='Tasks')
    draft_req_state = fields.Selection([
    ('draft', 'Draft'), 
    ('confirmed', 'Confirmed')], default='draft', string='Draft Status', tracking=True)
