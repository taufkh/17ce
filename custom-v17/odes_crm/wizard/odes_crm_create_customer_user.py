# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class OdesCrmCreateCustomerUser(models.TransientModel):
    _name = 'odes.crm.create.customer.user.wizard'
    _description = 'Create Customer User'

    @api.model
    def _default_company_id(self):
        context = self.env.context
        if context.get('active_model') == 'project.project' and context.get('active_id'):
            project = self.env['project.project'].browse(context['active_id'])
            return project.company_id.id

        return self.env['res.company']

    def action_confirm(self):
        self.ensure_one()
        context = self.env.context

        if context.get('active_model') != 'project.project' or not context.get('active_id'):
            raise UserError(_('Error occured, please refresh your screen and try again.'))

        default_user = self.env.ref('odes_crm.odes_default_client_user')
        if not default_user.exists():
            raise ValueError(_('Default user template not found, please contact support.'))

        values = {
            'active': True,
            'name': self.name,
            'login': self.email,
            'email': self.email,
        }

        new_user = default_user.sudo().with_context(no_reset_password=False).copy(values)

        group_user = self.env.ref('base.group_user', False)
        group_portal = self.env.ref('base.group_portal', False)

        if group_user:
            group_user.sudo().write({
                'users': [(3, new_user.id)]
            })

        if group_portal:
            group_portal.sudo().write({
                'users': [(4, new_user.id)]
            })

        self.env['project.project'].browse(context['active_id']).write({
            'customer_user_ids': [(4, new_user.id)],
            'allowed_portal_user_ids': [(4, new_user.id)]
        })

        template = self.env.ref('odes_crm.mail_template_odes_crm_project_platform_account_created', raise_if_not_found=False)
        if template:
            template.sudo().send_mail(self.id, force_send=True)

        return True

    name = fields.Char('Name')
    email = fields.Char('Email')
    company_id = fields.Many2one('res.company', default=_default_company_id, string='Company')