from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ApprovalCategory(models.Model):
    _inherit = "approval.category"

    flow = fields.Selection([('manager_director', 'Staff -> Manager -> Director'), ('finance', 'Staff -> Finance')], string='Approval Flow', default='manager_director')
    is_expense = fields.Boolean('Expense', default=False)
    is_leave = fields.Boolean('Leave', default=False)

    def _compute_request_to_validate_count(self):
        super(ApprovalCategory, self)._compute_request_to_validate_count()
        for category in self:
            if category.is_expense:
                self.env.cr.execute("""
                    SELECT COALESCE(COUNT(id), 0) from hr_expense_sheet
                    where state = 'submit'
                    and user_id = %s
                """, (self.env.user.id,))

                category.request_to_validate_count = self.env.cr.fetchone()[0]

            elif category.is_leave:
                self.env.cr.execute("""
                    SELECT COALESCE(COUNT(id), 0) from hr_leave
                    where state = 'confirm'
                    and approver_id = %s 
                """, (self.env.user.id,))

                # leave_count = self.env['hr.leave'].sudo().search_count([('state','=','confirm'),'|',('approver_id','=',self.env.user.id),('employee_id.leave_manager_id','=',self.env.user.id)])

                # category.request_to_validate_count = leave_count
                category.request_to_validate_count = self.env.cr.fetchone()[0]


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    follower_ids = fields.Many2many('res.users', 'approval_request_res_users_rel', 'request_id','user_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    def action_confirm(self):
        # if len(self.approver_ids) < self.approval_minimum:
        #     raise UserError(_("You have to add at least %s approvers to confirm your request.", self.approval_minimum))
        if self.requirer_document == 'required' and not self.attachment_number:
            raise UserError(_("You have to attach at lease one document."))

        if self.category_id.flow == 'manager_director':
            next_pending_user = self.get_approval_user('manager')
            # if (not next_pending_user or next_pending_user.is_director) and not self.env.user.is_finance:
            #     next_pending_user = self.get_approval_user('finance')
            if not next_pending_user:
                next_pending_user = self.get_approval_user('director')
            if not next_pending_user:
                raise UserError(_("You don't have any approver."))
        elif self.category_id.flow == 'finance':
            next_pending_user = self.get_approval_user('finance')
            if not next_pending_user:
                raise UserError(_("You don't have any approver."))
        else:
            raise UserError(_("You don't have any approver."))

        approvers = self.mapped('approver_ids').filtered(lambda approver: approver.status == 'new' and approver.user_id == next_pending_user)
        approvers._create_activity()
        approvers.write({'status': 'pending'})
        self.write({'date_confirmed': fields.Datetime.now()})

    def action_approve(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approver.write({'status': 'approved'})
        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

        user = self.env.user
        next_pending_user = False
        # if user.is_finance:
        #     next_pending_user = self.get_approval_user('director')
        # elif not user.is_director:
        #     next_pending_user = self.get_approval_user('finance')

        # if not user.is_director and next_pending_user:
        if self.category_id.flow == 'manager_director':
            next_pending_user = self.get_approval_user('director')
        elif self.category_id.flow == 'finance':
            next_pending_user = False
        else:
            raise UserError(_("You don't have any approver."))
        if next_pending_user:
            print('testtt')
            approvers = self.mapped('approver_ids').filtered(lambda approver: approver.status == 'new' and approver.user_id == next_pending_user)
            approvers.sudo()._create_activity()
            approvers.write({'status': 'pending'})

    @api.depends('approver_ids.status')
    def _compute_request_status(self):
        for request in self:
            status_lst = request.mapped('approver_ids.status')
            # minimal_approver = request.approval_minimum if len(status_lst) >= request.approval_minimum else len(status_lst)
            if status_lst:
                if status_lst.count('cancel'):
                    status = 'cancel'
                elif status_lst.count('refused'):
                    status = 'refused'
                elif status_lst.count('pending'):
                    status = 'pending'
                elif status_lst.count('new'):
                    status = 'new'
                # elif status_lst.count('approved') >= minimal_approver:
                #     status = 'approved'
                elif status_lst.count('approved'):
                    status = 'approved'
                else:
                    status = 'pending'
            else:
                status = 'new'
            request.request_status = status

    @api.onchange('category_id', 'request_owner_id')
    def _onchange_category_id(self):
        current_users = self.approver_ids.mapped('user_id')
        # new_users = self.category_id.user_ids
        # if self.category_id.is_manager_approver:
        #     employee = self.env['hr.employee'].search([('user_id', '=', self.request_owner_id.id)], limit=1)
        #     if employee.parent_id.user_id:
        #         new_users |= employee.parent_id.user_id
        new_users = self.env['res.users']
        # new_users = self.get_approval_user('all')
        if self.category_id.flow == 'manager_director':
            new_users |= self.get_approval_user('manager')
            new_users |= self.get_approval_user('director')
        elif self.category_id.flow == 'finance':
            new_users |= self.get_approval_user('finance')
        else:
            raise UserError(_("Please set the Approval Flow in the Category"))
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

    def get_approval_user(self, user_type):
        users = self.env['res.users']
        user_obj = self.env['res.users'].sudo()
        if user_type == 'all':
            employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.request_owner_id.id)], limit=1)
            manager_user = employee.parent_id.user_id
            if manager_user and not manager_user.is_finance and not manager_user.is_director:
                users |= manager_user

            finance_users = user_obj.search([('is_finance', '=', True)], limit=1)
            if finance_users:
                users |= finance_users

            director_users = user_obj.search([('is_director', '=', True)], limit=1)
            if director_users:
                users |= director_users

        elif user_type == 'manager':
            employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.request_owner_id.id)], limit=1)
            manager_user = employee.parent_id.user_id
            if manager_user:# and not manager_user.is_finance and not manager_user.is_director:
                users |= manager_user

        elif user_type == 'finance':
            finance_users = user_obj.search([('is_finance', '=', True)], limit=1)
            if finance_users:
                users |= finance_users

        elif user_type == 'director':
            director_users = user_obj.search([('is_director', '=', True)], limit=1)
            if director_users:
                users |= director_users

        return users