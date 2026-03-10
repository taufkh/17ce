# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta

class OdesCrmRejectDcrWizard(models.TransientModel):
    _name = 'odes.crm.reject.dcr.wizard'
    _description = 'Reject Deadline Change Request'

    def action_confirm(self):
        dcr_id = self._context.get('active_id')
        dcr = self.env['odes.crm.deadline.change.approvement'].browse(dcr_id)
        dcr.rejected_reason = self.reason
        dcr.is_rejected_by_coo = True

        template = self.env.ref('odes_crm.mail_template_odes_crm_reject_dcr', raise_if_not_found=False)

        if template:
            template.sudo().send_mail(dcr.id, force_send=True)

    reason = fields.Text('Reason')