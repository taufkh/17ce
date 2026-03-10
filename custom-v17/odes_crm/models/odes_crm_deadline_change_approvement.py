# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class OdesCrmDeadlineChangeApprovement(models.Model):
    _name = 'odes.crm.deadline.change.approvement'
    _description = 'Deadline Change Approvement'

    def action_approve(self):
        self.is_approved_by_coo = True

        self.req_id.date_deadline = self.new_deadline

    def action_reject(self):
        return {
            'name': _('Reject Deadline Change Request'),
            'view_mode': 'form',
            'res_model': 'odes.crm.reject.dcr.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def _compute_approvement_url(self):
        for rec in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            second_url = '/web#id='
            third_url = '&view_type=form&model=odes.crm.deadline.change.approvement&action='
            action = self.env['ir.actions.actions']._for_xml_id('odes_crm.action_odes_crm_deadline_change_approvement')

            rec.approvement_url = base_url + second_url + str(rec.id) + third_url + str(action['id'])

    name = fields.Char('Description')
    requested_date = fields.Date('Requested Date')
    new_deadline = fields.Date('New Deadline')
    reason = fields.Text('Reason')
    rejected_reason = fields.Text('Rejected Reason')
    req_id = fields.Many2one('odes.crm.requirement', 'Req')
    project_id = fields.Many2one('project.project', string='Project')
    req_number = fields.Char(string='REQ')
    current_deadline = fields.Date(string='Current Deadline', related='req_id.date_deadline')
    is_approved_by_coo = fields.Boolean('Approved by COO')
    is_rejected_by_coo = fields.Boolean('Rejected by COO')
    approvement_url = fields.Char(string='Approvement URL', compute='_compute_approvement_url')
    company_id = fields.Many2one('res.company', string='Company')