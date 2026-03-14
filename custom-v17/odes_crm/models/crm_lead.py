# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ast import literal_eval

class Lead(models.Model):
    _inherit = 'crm.lead'

    def action_create_user(self):
        self.ensure_one()
        if not self.email_from:
            raise UserError(_('Please fill in customer\'s email to create user'))     

        default_user = self.env.ref('odes_crm.odes_default_client_user')
        if not default_user.exists():
            raise ValueError(_('Default user template not found, please contact support.'))

        values = {
            'active': True,
            'name': self.name,
            'login': self.email_from,
            'email': self.email_from,
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

        nda = self.env['odes.crm.nda'].create({
           'opportunity_id': self.id,
           'user_id': new_user.id,     
        })

        self.write({
            'customer_user_id': new_user.id,
            'nda_id': nda.id
        })

        if self.project_ids:
            self.project_ids.write({
                'customer_user_ids': [(4, new_user.id)],
                'allowed_portal_user_ids': [(4, new_user.id)]
            })

        template = self.env.ref('odes_crm.mail_template_odes_crm_platform_account_created', raise_if_not_found=False)
        if template:
            template.sudo().send_mail(self.id, force_send=True)

        return True

    def create_project(self):
        self.ensure_one()

        project_ids = super(Lead, self).create_project()
        if project_ids and self.customer_user_id:
            self.env['project.project'].browse(project_ids).write({
                'customer_user_ids': [(4, self.customer_user_id.id)],
                'allowed_portal_user_ids': [(4, self.customer_user_id.id)]
            })

        return project_ids

    @api.depends('company_id')
    def _compute_is_odes_crm(self):
        for lead in self:
            lead.is_odes_crm = False
            if lead.company_id:
                param_company_id = literal_eval(self.env['ir.config_parameter'].sudo().get_param('odes_crm.crm_create_user_company_id', 'False'))
                lead.is_odes_crm = (lead.company_id.id == param_company_id) and True or False

    @api.depends('nda_id', 'nda_id.state')
    def _compute_is_nda_confirmed(self):
        for lead in self:
            lead.is_nda_confirmed = False
            if lead.nda_id:
                lead.is_nda_confirmed = lead.nda_id.state == 'confirmed' and True or False

    def action_view_nda(self):
        self.ensure_one()
        view_id = self.env['ir.model.data'].xmlid_to_res_id('odes_crm.view_odes_crm_nda_form')
        return {
            'name': _('NDA'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'odes.crm.nda',
            'res_id': self.nda_id and self.nda_id.id or False,
            'views': [[view_id, 'form']]
        }

    customer_user_id = fields.Many2one('res.users', string='Customer User')
    nda_id = fields.Many2one('odes.crm.nda', string='NDA')
    is_odes_crm = fields.Boolean(compute='_compute_is_odes_crm', string='ODES CRM')
    is_nda_confirmed = fields.Boolean(compute='_compute_is_nda_confirmed', string='NDA Confirmed', store=True)