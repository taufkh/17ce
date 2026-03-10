# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import html2plaintext
import math
from datetime import timedelta,datetime

class HrExpense(models.Model):
    _inherit = "hr.expense"

    expense_approved_dates = fields.Datetime('Approved Date')

    @api.depends('sheet_id', 'sheet_id.account_move_ids', 'sheet_id.state')
    def _compute_state(self):
        res = super(HrExpense, self)._compute_state()
        for expense in self:
            if expense.sheet_id and expense.sheet_id.state == "done":
                expense.state = "done"
        return res

class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    _sql_constraints = [
        ('journal_id_required_posted', 'CHECK(1=1)', 'This is unique!')
    ]

    def _get_approved_date(self):
        for rec in self:
            if rec.expense_line_ids:
                rec.expense_approved_dates = rec.expense_line_ids[0].expense_approved_dates
            else:
                rec.expense_approved_dates = False


    journal_id = fields.Many2one('account.journal', default=False)
    bank_journal_id = fields.Many2one('account.journal', default=False)
    paid_date = fields.Date('Paid Date')
    expense_approved_dates = fields.Datetime("Approved Date", compute='_get_approved_date')

    def update_to_posted(self):
        self.state = 'post'


    # def approve_expense_sheets(self):
    #     approver = False
    #     ###IF Finance, auto able to approve
    #     if self.env.user.is_finance and not self.is_finance:
    #         approver = self.get_approver_user('finance')
    #     elif not self.is_manager:
    #         approver = self.get_approver_user('manager')
    #     elif not self.is_finance:
    #         approver = self.get_approver_user('finance')
    #     elif not self.is_director:
    #         approver = self.get_approver_user('director')
    #     if not approver:
    #         raise UserError(_('No Approver exist, Please Reset to Draft and Re-Submit to Manager'))
    #     if self.env.user != approver:
    #         if approver.is_finance:
    #             raise UserError(_('The expenses is waiting "Finance" to approve'))
    #         elif approver.is_director:
    #             raise UserError(_('The expenses is waiting "Director" to approve'))
    #         else:
    #             raise UserError(_('The expenses is waiting "Manager" to approve'))

    #     ###IF Finance, auto able to approve
    #     if self.env.user.is_finance and not self.is_finance:
    #         self.filtered(lambda hol: hol.state == 'submit').activity_feedback(['hr_expense.mail_act_expense_approval'])
    #         self.is_manager = True
    #         self.is_finance = True
    #         new_approver = self.get_approver_user('director')
    #     elif not self.is_manager:
    #         self.filtered(lambda hol: hol.state == 'submit').activity_feedback(['hr_expense.mail_act_expense_approval'])
    #         self.is_manager = True
    #         new_approver = self.get_approver_user('finance')
    #     elif not self.is_finance:
    #         self.filtered(lambda hol: hol.state == 'submit').activity_feedback(['hr_expense.mail_act_expense_approval'])
    #         self.is_finance = True
    #         new_approver = self.get_approver_user('director')
    #     elif not self.is_director:
    #         self.is_director = True
    #         new_approver = approver
    #         self.write({'state': 'approve'})
    #     expense_id = self.env['hr.expense'].search([('sheet_id','=',self.id)])
    #     if expense_id:
    #         expense_id.write({'expense_approved_dates':datetime.now()})
    #     self.user_id = new_approver.id
    #     self.activity_update()

    def set_to_paid(self):
        self.state = 'done'        
        self.paid_date = fields.Date.today()
