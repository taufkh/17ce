from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import html2plaintext
import math
from datetime import datetime,timedelta

class ApprovalRequest(models.Model):
    _inherit = "approval.request"

    # follower_ids = fields.Many2many('res.users', 'approval_request_res_users_rel', 'request_id','user_id')
    # currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    odes_approval_dates = fields.Datetime('Approval Date')
    def action_approve(self, approver=None):
        
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approver.write({'status': 'approved'})
        approve_state = []
        for app in self.approver_ids:
            approve_state.append(app.status)
        result = all(element == 'approved' for element in approve_state)
        if result:
            self.odes_approval_dates = datetime.now()

        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

        if self.category_id.flow == 'finance_and_director':
            next_pending_user = False
            manager = self.get_approval_user('manager')
            finance = self.get_approval_user('finance')
            director = self.get_approval_user('director')
            for rec in self.approver_ids:
                if rec.user_id.id == manager.id and rec.status == 'approved':
                    next_pending_user = self.get_approval_user('finance')
                if rec.user_id.id == finance.id and rec.status == 'approved':
                    next_pending_user = self.get_approval_user('director')
            
                if not next_pending_user:
                    next_pending_user = False
                
            if next_pending_user:
                approvers = self.mapped('approver_ids').filtered(lambda approver: approver.status == 'new' and approver.user_id == next_pending_user)
                approvers._create_activity()
                approvers.write({'status': 'pending'})
    
        else:
            return super(ApprovalRequest, self).action_approve()

    @api.onchange('category_id', 'request_owner_id')
    def _onchange_category_id(self):
        current_users = self.approver_ids.mapped('user_id')
        new_users = self.env['res.users']
        if self.category_id.flow == 'finance_and_director':
            new_users |= self.get_approval_user('manager')
            new_users |= self.get_approval_user('finance')
            new_users |= self.get_approval_user('director')


            for user in new_users - current_users - self.env.user:
                self.approver_ids += self.env['approval.approver'].new({
                    'user_id': user.id,
                    'request_id': self.id,
                    'status': 'new'})
            
            if not self.approver_ids:
                if self.category_id.flow == 'manager_director':
                    user = self.get_approval_user('director')
                elif self.category_id.flow == 'finance':
                    user = self.get_approval_user('finance')
                else:
                    raise UserError(_("Please set the Approval Flow in the Category"))
                self.approver_ids += self.env['approval.approver'].new({
                    'user_id': user.id,
                    'request_id': self.id,
                    'status': 'new'})

        else:
            return super(ApprovalRequest, self)._onchange_category_id()
    
    def action_confirm(self):
        if self.category_id.flow == 'finance_and_director':
            next_pending_user = self.get_approval_user('manager')
            if not next_pending_user:
                next_pending_user = self.get_approval_user('finance')
                if not next_pending_user:
                    next_pending_user = self.get_approval_user('director')
                    if not next_pending_user:
                        raise UserError(_("You don't have any approver."))
        
            approvers = self.mapped('approver_ids').filtered(lambda approver: approver.status == 'new' and approver.user_id == next_pending_user)
            approvers._create_activity()
            approvers.write({'status': 'pending'})
            self.write({'date_confirmed': fields.Datetime.now()})
        
        else:
            return super(ApprovalRequest, self).action_confirm()

class ApprovalCategory(models.Model):
    _inherit = "approval.category"

    flow = fields.Selection(selection_add=[('finance_and_director','Staff -> Manager -> Finance -> Director')])

#     flow = fields.Selection([('manager_director', 'Staff -> Manager -> Director'), ('finance', 'Staff -> Finance')], string='Approval Flow', default='manager_director')
#     is_expense = fields.Boolean('Expense', default=False)
#     is_leave = fields.Boolean('Leave', default=False)