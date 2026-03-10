# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from ast import literal_eval

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model_create_multi
    def create(self, vals_list):
        #skip NDA check is system parameter have "odes_crm.bypass_nda" as True
        bypass_nda = self.env['ir.config_parameter'].sudo().get_param('odes_crm.bypass_nda')

        for vals in vals_list:
            if vals.get('opportunity_id'):
                opportunity = self.env['crm.lead'].browse(vals['opportunity_id'])
                if opportunity.is_odes_crm and not opportunity.is_nda_confirmed and not bypass_nda:
                    raise UserError(_('You can only create quotation with NDA that has been confirmed.'))

                if not opportunity.is_odes_crm:
                    vals['odes_crm_doc_ids'] = [(6, 0, [])]

            if vals.get('pm_user_id') and not self.env.user.has_group('odes_crm.group_odes_c_level'):
                raise UserError(_('Only C-Level users are allowed to edit Project Manager.'))

        records = super(SaleOrder, self).create(vals_list)

        for vals, rec in zip(vals_list, records):
            is_send_upload_mail = False
            if vals.get('odes_crm_doc_ids'):
                for odes_crm_doc in vals['odes_crm_doc_ids']:
                    if len(odes_crm_doc) > 1 and odes_crm_doc[2]:
                        doc_attachment = odes_crm_doc[2].get('attachment_ids')
                        upload_user_id = odes_crm_doc[2].get('upload_user_id')

                        if upload_user_id:
                            upload_user = self.env['res.users'].browse(upload_user_id)
                            if upload_user.has_group('odes_crm.group_odes_customer') and doc_attachment and len(doc_attachment[0]) > 1 and doc_attachment[0][2]:
                                is_send_upload_mail = True
                                break

            if is_send_upload_mail:
                template = self.env.ref('odes_crm.mail_template_odes_crm_client_upload_doc', raise_if_not_found=False)
                if template:
                    template.sudo().send_mail(rec.id, force_send=True, email_values={'attachments': []})

        return records

    def write(self, values):
        #skip NDA check is system parameter have "odes_crm.bypass_nda" as True
        bypass_nda = self.env['ir.config_parameter'].sudo().get_param('odes_crm.bypass_nda')

        if values.get('opportunity_id'):
            opportunity = self.env['crm.lead'].browse(values['opportunity_id'])
            if opportunity.is_odes_crm and not opportunity.is_nda_confirmed and not bypass_nda:
                raise UserError(_('You can only create quotation with NDA that has been confirmed.'))

            if not opportunity.is_odes_crm:
                values['odes_crm_doc_ids'] = [(6, 0, [])]

        if values.get('pm_user_id') and not self.env.user.has_group('odes_crm.group_odes_c_level'):
            raise UserError(_('Only C-Level users are allowed to edit Project Manager.'))

        is_send_upload_mail = False
        if values.get('odes_crm_doc_ids'):
            for odes_crm_doc in values['odes_crm_doc_ids']:
                if len(odes_crm_doc) > 1 and odes_crm_doc[2]:
                    doc_attachment = odes_crm_doc[2].get('attachment_ids')
                    upload_user_id = odes_crm_doc[2].get('upload_user_id')

                    if upload_user_id:
                        upload_user = self.env['res.users'].browse(upload_user_id)
                        if upload_user.has_group('odes_crm.group_odes_customer') and doc_attachment and len(doc_attachment[0]) > 1 and doc_attachment[0][2]:
                            is_send_upload_mail = True
                            break

        if is_send_upload_mail:
            template = self.env.ref('odes_crm.mail_template_odes_crm_client_upload_doc', raise_if_not_found=False)
            if template:
                template.sudo().send_mail(self.id, force_send=True, email_values={'attachments': []})

        res = super(SaleOrder, self).write(values)
        return res

    @api.model
    def default_get(self, fields):
        res = super(SaleOrder, self).default_get(fields)
        context = self.env.context

        if context.get('default_opportunity_id'):
            opportunity = self.env['crm.lead'].browse(context['default_opportunity_id'])
            if opportunity.is_odes_crm:
                odes_crm_doc_ids = []
                param_company_id = literal_eval(self.env['ir.config_parameter'].sudo().get_param('odes_crm.crm_create_user_company_id', 'False'))
                company = self.env['res.company'].browse(param_company_id)

                for config in company.doc_config_ids:
                    odes_crm_doc_ids.append((0, 0, {
                        'sequence': config.sequence,
                        'name': config.name,
                        'title_id': config.title_id.id
                    }))

                res['odes_crm_doc_ids'] = odes_crm_doc_ids

                res['partner_id'] = res['partner_invoice_id'] = res['partner_shipping_id'] = opportunity.customer_user_id and opportunity.customer_user_id.partner_id.id or False

        return res

    @api.onchange('opportunity_id')
    def _onchange_opportunity_id(self):
        if self.opportunity_id:
            if self.opportunity_id.is_odes_crm:
                odes_crm_doc_ids = [(6, 0, [])]
                param_company_id = literal_eval(self.env['ir.config_parameter'].sudo().get_param('odes_crm.crm_create_user_company_id', 'False'))
                company = self.env['res.company'].browse(param_company_id)

                for config in company.doc_config_ids:
                    odes_crm_doc_ids.append((0, 0, {
                        'sequence': config.sequence,
                        'name': config.name,
                        'title_id': config.title_id.id
                    }))

                self.odes_crm_doc_ids = odes_crm_doc_ids

    @api.depends('odes_crm_doc_ids', 'odes_crm_doc_ids.state')
    def _compute_is_doc_acknowledged(self):
        for order in self:
            order.is_doc_acknowledged = all(doc.state == 'acknowledged' for doc in order.odes_crm_doc_ids)

    def _compute_order_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        second_url = '/web#id='
        third_url = '&view_type=form&model=sale.order&action='
        action = self.env['ir.actions.actions']._for_xml_id('sale.action_quotations_with_onboarding')

        for order in self:
            full_url = base_url+second_url+str(order.id)+third_url+str(action['id'])
            order.order_url = full_url

    def _compute_project_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        second_url = '/web#id='
        third_url = '&view_type=form&model=project.project&action='
        action = self.env['ir.actions.actions']._for_xml_id('project.open_view_project_all')

        for order in self:
            order.project_url = False
            if order.opportunity_id:
                project = self.env['project.project'].search([('lead_id', '=', order.opportunity_id.id)], limit=1)
                if project:
                    full_url = base_url+second_url+str(project.id)+third_url+str(action['id'])
                    order.project_url = full_url

    def action_doc_request_approval(self):
        self.ensure_one()

        if not self.user_id:
            raise UserError(_('Salesperson is not defined!'))

        c_level_users = self.env.ref('odes_crm.group_odes_c_level').users
        if c_level_users:
            c_level_partner_ids = [user.partner_id.id for user in c_level_users]
            template = self.env.ref('odes_crm.mail_template_odes_crm_request_c_level_approval', raise_if_not_found=False)
            if template:
                template.sudo().send_mail(self.id, force_send=True, email_values={'recipient_ids': c_level_partner_ids, 'attachments': []})

        self.write({
            'doc_approval_state': 'requested',
            'doc_date_requested': fields.Datetime.now()
        })

    def action_doc_approve(self):
        self.ensure_one()

        if not self.user_id:
            raise UserError(_('Salesperson is not defined!'))

        if not self.pm_user_id:
            raise UserError(_('Please assign a project manager before approve.'))

        bd_template = self.env.ref('odes_crm.mail_template_odes_crm_c_level_approve', raise_if_not_found=False)
        if bd_template:
            bd_template.sudo().send_mail(self.id, force_send=True, email_values={'attachments': []})

        pm_template = self.env.ref('odes_crm.mail_template_odes_crm_c_level_pm_assigned', raise_if_not_found=False)
        if pm_template:
            pm_template.sudo().send_mail(self.id, force_send=True, email_values={'attachments': []})

        self.write({
            'doc_approval_state': 'approved',
            'doc_date_approved': fields.Datetime.now(),
            'doc_approved_user_id': self.env.user.id
        })

    def action_view_requirement(self):
        self.ensure_one()

        domain = [('order_id', '=', self.id)]
        context = {'default_order_id': self.id}

        if self.opportunity_id:
            projects = self.env['project.project'].search([('lead_id', '=', self.opportunity_id.id)])
            if projects:
                domain = ['|', ('order_id', '=', self.id), ('project_id', 'in', projects._ids)]
                context['default_project_id'] = projects[0].id

        return {
            'name': 'Requirements',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form,gantt',
            'res_model': 'odes.crm.requirement',
            'domain': domain,
            'context': context
        }

    def action_view_calendar(self):
        self.ensure_one()

        action = self.env['ir.actions.actions']._for_xml_id('calendar.action_calendar_event')
        partner = self.env.user.partner_id
        if partner:
            action['context'] = {
                'default_partner_ids': [partner.id]
            }
            action['domain'] = [('id', 'in', partner.meeting_ids.ids)]

        return action

    odes_crm_doc_ids = fields.One2many('odes.crm.doc', 'order_id', string='Documentations')
    is_odes_crm = fields.Boolean(related='opportunity_id.is_odes_crm', string='ODES CRM')
    is_nda_confirmed = fields.Boolean(related='opportunity_id.is_nda_confirmed', string='NDA Confirmed')
    is_doc_acknowledged = fields.Boolean(compute='_compute_is_doc_acknowledged', string='Doc. Acknowledged', store=True)
    doc_date_requested = fields.Datetime('Doc. Approval Requested Date')
    doc_date_approved = fields.Datetime('Doc. Approved Date')
    doc_approved_user_id = fields.Many2one('res.users', string='Doc. Approved User')
    doc_approval_state = fields.Selection([('waiting', 'Waiting Approval Request'), ('requested', 'Approval Requested'), ('approved', 'Approved')], default='waiting', string='Doc. Approval Status')
    odes_crm_requirement_ids = fields.One2many('odes.crm.requirement', 'order_id', string='Requirements')
    odes_crm_module_expert_ids = fields.One2many('odes.crm.module.expert', 'order_id', string='Module Subject Expert')
    pm_user_id = fields.Many2one('res.users', string='Project Manager')
    order_url = fields.Char(compute='_compute_order_url', string='Order Url')
    project_url = fields.Char(compute='_compute_project_url', string='Project Url')
