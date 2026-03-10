# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

class OdesCrmDeadlineChangeRequest(models.TransientModel):
    _name = 'odes.crm.deadline.change.request.wizard'
    _description = 'Deadline Change Request'

    def action_confirm(self):
        if self.new_deadline > date.today():
            req_id = self._context.get('active_id')
            req = self.env['odes.crm.requirement'].browse(req_id)
            deadline_change_approvement_obj = self.env['odes.crm.deadline.change.approvement'].sudo()

            deadline_change_approvement = deadline_change_approvement_obj.create({
                'name': 'Deadline Change for ' + req.number,
                'new_deadline': self.new_deadline,
                'reason': self.reason,
                'req_id': req_id,
                'company_id': req.company_id.id,
                'requested_date': date.today(),
                'project_id': req.project_id.id,
                'req_number': req.number,
            })

            template = self.env.ref('odes_crm.mail_template_odes_crm_deadline_change_request', raise_if_not_found=False)

            if template:
                template.sudo().send_mail(deadline_change_approvement.id, force_send=True)
        else:
            raise ValidationError("New Deadline cannot be the less or the same as the Current Deadline.")

    new_deadline = fields.Date('New Deadline')
    reason = fields.Text('Reason')