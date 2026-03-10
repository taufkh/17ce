# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date
from collections import defaultdict
import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    paid_date = fields.Date(string='Paid Date', index=True, copy=False,
                                    compute='_compute_paid_date', store=True, readonly=False,
                                    help="The date when the invoice was paid.")

    @api.depends('payment_state', 'payment_ids')
    def _compute_paid_date(self):
        AccountPayment = self.env['account.payment']
        for rec in self:
            paid_date = False
            
            if rec.invoice_payments_widget:
                paid_date = max([x.get('date') for x in rec.invoice_payments_widget.get('content')])
                    
            rec.paid_date = paid_date

    def _reverse_moves(self, default_values_list=None, cancel=False):
        res = super()._reverse_moves(default_values_list=default_values_list, cancel=False)
        return res


class HrExpense(models.Model):
    _inherit = 'hr.expense'
    
    def action_submit_expenses(self):
        today = fields.Date.context_today(self)
        if today.day > 20 and not self.env.user.has_group('hr_expense.group_hr_expense_manager'):
            raise ValidationError('Expense cannot be submitted after the 20th of this month unless override is granted. Please contact Finance for exceptions.')
        
        res = super().action_submit_expenses()
        return res

class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    def action_submit_sheet(self):
        today = fields.Date.context_today(self)
        if today.day > 20 and not self.env.user.has_group('hr_expense.group_hr_expense_manager'):
            raise ValidationError('Expense cannot be submitted after the 20th of this month unless override is granted. Please contact Finance for exceptions.')

        res = super().action_submit_sheet()
        return res
