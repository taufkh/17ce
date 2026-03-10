# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    is_manager = fields.Boolean('Manager Approve', default=False)
    is_finance = fields.Boolean('Finance Approve', default=False)
    is_director = fields.Boolean('Director Approve', default=False)

    sgd_currency_id = fields.Many2one('res.currency', 'SGD Currency', default=lambda self: self.env.ref('base.SGD').id)
    sgd_total = fields.Float('SGD Total Amount', compute='_compute_amount', compute_sudo=True)
    line_total = fields.Float('Line Total Amount', compute='_compute_amount', compute_sudo=True)
    line_currency_id = fields.Many2one('res.currency', 'Line Currency')

    @api.depends('expense_line_ids.total_amount', 'expense_line_ids.sgd_total', 'expense_line_ids.currency_id')
    def _compute_amount(self):
        res = super(HrExpenseSheet, self)._compute_amount()
        for sheet in self:
            sheet.sgd_total = sum(sheet.expense_line_ids.mapped('sgd_total'))
            if len(sheet.expense_line_ids.currency_id) > 1:
                raise UserError(_('You cannot report expenses for different currencies in the same report.'))
            sheet.line_currency_id = sheet.expense_line_ids and sheet.expense_line_ids.currency_id.id or False
            sheet.line_total = sum(sheet.expense_line_ids.mapped('total_amount'))

    # def action_submit_sheet(self):
    #     approver = self.get_approver_user('manager')
    #     if (not approver or approver.is_director) and not self.env.user.is_finance:
    #         approver = self.get_approver_user('finance')
    #     if not approver:
    #         approver = self.get_approver_user('director')
    #     if not approver:
    #         raise UserError(_('No Approver exist, Please Reset to Draft and Re-Submit to Manager'))

    #     if self.env.user.is_finance or self.env.user.is_director:
    #         self.is_manager = True
    #         self.is_finance = True
    #         self.is_director = False
    #         approver = approver = self.get_approver_user('director')
    #     elif approver.is_finance:
    #         self.is_manager = True
    #         self.is_finance = False
    #         self.is_director = False
    #     elif approver.is_director:
    #         self.is_manager = True
    #         self.is_finance = True
    #         self.is_director = False
    #     else:
    #         self.is_manager = False
    #         self.is_finance = False
    #         self.is_director = False

    #     self.user_id = approver.id
        
    #     res = super(HrExpenseSheet, self).action_submit_sheet()
    #     return res

    def approve_expense_sheets(self):
        # if not self.user_has_groups('hr_expense.group_hr_expense_team_approver'):
        #     raise UserError(_("Only Managers and HR Officers can approve expenses"))
        # elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
        #     current_managers = self.employee_id.expense_manager_id | self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id

        #     if self.employee_id.user_id == self.env.user:
        #         raise UserError(_("You cannot approve your own expenses"))

        #     if not self.env.user in current_managers and not self.user_has_groups('hr_expense.group_hr_expense_user') and self.employee_id.expense_manager_id != self.env.user:
        #         raise UserError(_("You can only approve your department expenses"))

        # responsible_id = self.user_id.id or self.env.user.id
        # self.write({'state': 'approve', 'user_id': responsible_id})
        # self.activity_update()
        approver = False
        ###IF Finance, auto able to approve
        if self.env.user.is_finance and not self.is_finance:
            approver = self.get_approver_user('finance')
        elif not self.is_manager:
            approver = self.get_approver_user('manager')
        elif not self.is_finance:
            approver = self.get_approver_user('finance')
        elif not self.is_director:
            approver = self.get_approver_user('director')
        if not approver:
            raise UserError(_('No Approver exist, Please Reset to Draft and Re-Submit to Manager'))
        if self.env.user != approver:
            if approver.is_finance:
                raise UserError(_('The expenses is waiting "Finance" to approve'))
            elif approver.is_director:
                raise UserError(_('The expenses is waiting "Director" to approve'))
            else:
                raise UserError(_('The expenses is waiting "Manager" to approve'))

        ###IF Finance, auto able to approve
        if self.env.user.is_finance and not self.is_finance:
            self.filtered(lambda hol: hol.state == 'submit').activity_feedback(['hr_expense.mail_act_expense_approval'])
            self.is_manager = True
            self.is_finance = True
            new_approver = self.get_approver_user('director')

            reg = { 
               'res_id': self.id, 
               'res_model': 'hr.expense.sheet', 
               'partner_id': self.env.user.partner_id.id, 
            }
            
            if not self.env['mail.followers'].search([('res_id','=',self.id),('res_model','=','hr.expense.sheet'),('partner_id','=',self.env.user.partner_id.id)]): 
                follower_id = self.env['mail.followers'].sudo().create(reg)
            
        elif not self.is_manager:
            self.filtered(lambda hol: hol.state == 'submit').activity_feedback(['hr_expense.mail_act_expense_approval'])
            self.is_manager = True
            new_approver = self.get_approver_user('finance')
        elif not self.is_finance:
            self.filtered(lambda hol: hol.state == 'submit').activity_feedback(['hr_expense.mail_act_expense_approval'])
            self.is_finance = True
            new_approver = self.get_approver_user('director')
        elif not self.is_director:
            self.is_director = True
            new_approver = approver
            self.write({'state': 'approve'})
        
        self.user_id = new_approver.id
        self.activity_update()

    def get_approver_user(self, user_type):
        users = self.env['res.users']
        user_obj = self.env['res.users'].sudo()
        if user_type == 'all':
            employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.employee_id.user_id.id)], limit=1)
            manager_user = employee.parent_id.user_id
            if manager_user:
                users |= manager_user

            finance_users = user_obj.search([('is_finance', '=', True)], limit=1)
            if finance_users:
                users |= finance_users

            director_users = user_obj.search([('is_director', '=', True)], limit=1)
            if director_users:
                users |= director_users

        elif user_type == 'manager':
            employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.employee_id.user_id.id)], limit=1)
            manager_user = employee.parent_id.user_id
            if manager_user:
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

    def action_get_attachment_view(self):
        res = super(HrExpenseSheet, self).action_get_attachment_view()
        res['context'].update({'form_view_ref': 'odes_custom.odes_ir_attachment_view_form'})
        return res

class HrExpense(models.Model):
    _inherit = "hr.expense"

    def action_get_attachment_view(self):
        self.ensure_one()
        res = super(HrExpense, self).action_get_attachment_view()
        res['context'].update({'form_view_ref': 'odes_custom.odes_ir_attachment_view_form'})
        return res

    def action_attachment_report_view(self):
        self.ensure_one()
        if self.attachment_number == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Attachment',
                'view_mode': 'form',
                'res_model': 'ir.attachment',
                'domain': [('res_model', '=', 'hr.expense'), ('res_id', 'in', self.ids)],
                'context': {'default_res_model': 'hr.expense', 'default_res_id': self.id, 'form_view_ref': 'odes_custom.odes_ir_attachment_view_form', 'read_only': 1},
                'res_id': self.env['ir.attachment'].search([('res_model', '=', 'hr.expense'), ('res_id', '=', self.id)], limit=1).id,
                'target': 'new',
            }
        else:
            return self.action_get_attachment_view()

    @api.model
    def get_empty_list_help(self, help):
        return """
            <p class="o_view_nocontent_smiling_face">
                No expense found. Let's create one!
            </p><p>
                Once you have created your expense, submit it to your manager who will validate it.
            </p>
        """

    def _get_default_company(self):
        context = dict(self._context or {})
        if context.get('allowed_company_ids'):
            if self.env.user.company_id.id in context['allowed_company_ids']:
                return self.env.user.company_id
            else:
                return self.env.company    
        else:
            return self.env.company

    def _get_domain_company(self):
        context = dict(self._context or {})
        if context.get('allowed_company_ids'):
            return [('id', 'in', context['allowed_company_ids'])]
        else:
            return [('id', 'in', self.env.user.company_ids.ids)]

    sgd_total = fields.Float('SGD Total', compute='_get_sgd_value')
    sgd_currency_id = fields.Many2one('res.currency', 'SGD Currency', default=lambda self: self.env.ref('base.SGD').id)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=_get_default_company, domain=_get_domain_company)

    def get_sgd_value(self, value):
        self.ensure_one()
        currency = self.currency_id
        sg_currency = self.sgd_currency_id
        if currency == sg_currency:
            return value
        elif self.company_id:
            return currency._convert(value, sg_currency, self.company_id, self.date or fields.Date.today())
        else:
            return 0

    @api.depends('total_amount', 'date', 'currency_id', 'sgd_currency_id', 'company_id')
    def _get_sgd_value(self):
        for expense in self:
            expense.sgd_total = expense.get_sgd_value(expense.total_amount)
