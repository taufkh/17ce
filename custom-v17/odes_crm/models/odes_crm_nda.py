# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime
from ast import literal_eval

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

class OdesCrmNda(models.Model):
    _name = 'odes.crm.nda'
    _description = 'NDA'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('odes.crm.nda')
        records = super(OdesCrmNda, self).create(vals_list)
        return records

    def _default_nda_content(self):
        param_company_id = literal_eval(self.env['ir.config_parameter'].sudo().get_param('odes_crm.crm_create_user_company_id', 'False'))
        company = self.env['res.company'].browse(param_company_id)
        return company.nda_content

    def action_confirm(self):
        self.ensure_one()

        if not self.sudo().opportunity_id.user_id:
            raise UserError(_('Salesperson is not defined!'))

        if not self.date_nda:
            raise UserError(_('Please fill in the NDA date.'))

        if not self.company_name: 
            raise UserError(_('Please fill in the company name.'))

        if not self.uen:
            raise UserError(_('Please fill in the UEN.'))

        if not self.registered_address:
            raise UserError(_('Please fill in the registered address.'))

        if not self.short_name:
            raise UserError(_('Please fill in the short name.'))

        self.write({
            'state': 'confirmed',
            'date_confirm': fields.Datetime.now()    
        })

        template = self.env.ref('odes_crm.mail_template_odes_crm_nda_acknowledgement_completed', raise_if_not_found=False)
        if template:
            template.sudo().send_mail(self.sudo().opportunity_id.id, force_send=True)

    @api.depends('date_nda', 'company_name', 'uen', 'registered_address', 'short_name')
    def _compute_nda_display(self):
        for nda in self:
            content = nda.nda_content
            if nda.date_nda:
                content = content.replace('${day}', custom_strftime('{S}', nda.date_nda))
                content = content.replace('${date}', datetime.strftime(nda.date_nda, '%B, %Y'))
            if nda.company_name:
                content = content.replace('${company_name}', nda.company_name)
            if nda.uen:
                content = content.replace('${uen}', nda.uen)
            if nda.registered_address:
                content = content.replace('${registered_address}', nda.registered_address)
            if nda.short_name:
                content = content.replace('${short_name}', nda.short_name)

            nda.nda_display = content

    name = fields.Char('Reference Number')
    opportunity_id = fields.Many2one('crm.lead', string='Related Opportunity')
    nda_content = fields.Text('NDA Content', default=_default_nda_content)
    nda_display = fields.Text(compute='_compute_nda_display', string='NDA')
    user_id = fields.Many2one('res.users', string='Customer User')
    partner_id = fields.Many2one(related='user_id.partner_id', string='Customer Partner')
    date_nda = fields.Datetime('NDA Date', default=fields.Datetime.now())
    date_confirm = fields.Datetime('NDA Confirmed Date')
    company_name = fields.Char('Company Name')
    uen = fields.Char('UEN')
    registered_address = fields.Char('Registered Address')
    short_name = fields.Char('Short Name')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], default='draft', string='Status')
