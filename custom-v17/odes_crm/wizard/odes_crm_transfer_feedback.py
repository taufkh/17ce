# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class OdesCrmTransferFeedbackWizard(models.TransientModel):
    _name = 'odes.crm.transfer.feedback.wizard'
    _description = 'Transfer Feedback'

    @api.model
    def default_get(self, fields):
        res = super(OdesCrmTransferFeedbackWizard, self).default_get(fields)
        context= self.env.context
        if context.get('active_model') == 'odes.crm.requirement.feedback' and context.get('active_id', False):
            feedback = self.env['odes.crm.requirement.feedback'].browse(context['active_id'])
            if feedback:
                res['name'] = feedback.name
                res['date'] = feedback.date
                res['description'] = feedback.description
                res['attachment_ids'] = feedback.attachment_ids and feedback.attachment_ids.ids or False
                if feedback.requirement_id:
                    res['module_id'] = feedback.requirement_id.module_id and feedback.requirement_id.module_id.id or False
                    res['type'] = feedback.requirement_id.type

        return res

    def action_confirm(self):
        self.ensure_one()
        context= self.env.context
        if context.get('active_model') == 'odes.crm.requirement.feedback' and context.get('active_id', False):
            feedback = self.env['odes.crm.requirement.feedback'].browse(context['active_id'])

            if feedback:
                transferred_requirement = self.env['odes.crm.requirement'].create({
                    'name': self.name,
                    'module_id': self.module_id and self.module_id.id or False,
                    'type': self.type,
                    'date': self.date,
                    'description': self.description,
                    'attachment_ids': self.attachment_ids and self.attachment_ids.ids or False,
                    'order_id': feedback.requirement_id.order_id and feedback.requirement_id.order_id.id or False,
                    'project_id': feedback.requirement_id.project_id and feedback.requirement_id.project_id.id or False
                })

                feedback.write({
                    'state': 'transferred',
                    'transferred_requirement_id': transferred_requirement.id
                })

    name = fields.Char('Title')
    module_id = fields.Many2one('odes.crm.requirement.module', string='Module')
    type = fields.Selection([
        ('custom', 'Customization'), 
        ('semi', 'Semi-Customization'), 
        ('setup', 'Setup'),
        ('variation', 'Variation Order')], string='Type')
    date = fields.Date('Date')
    description = fields.Text('Description')
    attachment_ids = fields.Many2many('ir.attachment', 'odes_crm_transfer_feedback_attachment_ids', 'transfer_id', 'attachment_id', string='Attachments')