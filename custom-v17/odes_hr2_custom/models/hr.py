
import time
from odoo import api, fields, models, tools, exceptions, _
from datetime import date, datetime
from dateutil import rrule

from dateutil import parser, relativedelta

from odoo import SUPERUSER_ID
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DSDF
from odoo.osv import expression
from pytz import UTC
from odoo.tools import float_compare

class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    start_datetime = fields.Datetime("Start Datetime")
    end_datetime = fields.Datetime("End Datetime")
    duration = fields.Float("Duration")

    # @api.onchange('start_datetime','end_datetime')
    # def onchange_datetime(self):
    #     duration = 0
    #     if self.start_datetime and self.end_datetime:
    #         timer = self.end_datetime - self.start_datetime
    #         timer = timer.total_seconds() / 60
    #         duration = self.get_rounded_time(timer)
    #     self.duration = duration
    #     self.unit_amount = duration


    # @api.model
    # def default_get(self, fields):
    #     result = super(AnalyticLine, self).default_get(fields)
    #     if self._context.get('def_project_id'):
    #         result['project_id'] = self._context['def_project_id']
    #     return result
        

class LeaveReport(models.Model):
    _inherit = "hr.leave.report"

    # start_date = fields.Date('Start Date', readonly=True)
    # end_date = fields.Date('End Date', readonly=True)

    # def init(self):
    #     tools.drop_view_if_exists(self._cr, 'hr_leave_report')

    #     self._cr.execute("""
    #         CREATE or REPLACE view hr_leave_report as (
    #             SELECT row_number() over(ORDER BY leaves.employee_id) as id,
    #             leaves.employee_id as employee_id, leaves.name as name,
    #             leaves.number_of_days as number_of_days, leaves.leave_type as leave_type,
    #             leaves.category_id as category_id, leaves.department_id as department_id,
    #             leaves.holiday_status_id as holiday_status_id, leaves.state as state,
    #             leaves.holiday_type as holiday_type, leaves.date_from as date_from,
    #             leaves.date_to as date_to, leaves.payslip_status as payslip_status
    #             from (select
    #                 allocation.employee_id as employee_id,
    #                 allocation.private_name as name,
    #                 allocation.number_of_days as number_of_days,
    #                 allocation.category_id as category_id,
    #                 allocation.department_id as department_id,
    #                 allocation.holiday_status_id as holiday_status_id,
    #                 allocation.state as state,
    #                 allocation.holiday_type,
    #                 allocation.start_date as date_from,
    #                 allocation.end_date as date_to,
    #                 FALSE as payslip_status,
    #                 'allocation' as leave_type
    #             from hr_leave_allocation as allocation
    #             union all select
    #                 request.employee_id as employee_id,
    #                 request.private_name as name,
    #                 (request.number_of_days * -1) as number_of_days,
    #                 request.category_id as category_id,
    #                 request.department_id as department_id,
    #                 request.holiday_status_id as holiday_status_id,
    #                 request.state as state,
    #                 request.holiday_type,
    #                 request.date_from as date_from,
    #                 request.date_to as date_to,
    #                 request.payslip_status as payslip_status,
    #                 'request' as leave_type
    #             from hr_leave as request) leaves
    #         );
    #     """)


    # @api.model
    # def action_time_off_analysis(self):
    #     domain = [('holiday_type', '=', 'employee')]

    #     if self.env.context.get('active_ids'):
    #         domain+=[('employee_id', 'in', self.env.context.get('active_ids', []))]
    #         domain+=['|',('number_of_days','<',0),'|',('date_to','=',False),('date_to','>',fields.Datetime.now())]

    #     return {
    #         'name': _('Time Off Analysis'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'hr.leave.report',
    #         'view_mode': 'tree,pivot,form',
    #         'search_view_id': self.env.ref('hr_holidays.view_hr_holidays_filter_report').id,
    #         'domain': domain,
    #         'context': {
    #             'search_default_group_type': True,
    #             'search_default_year': True,
    #             'search_default_validated': True,
    #         }
    #     }


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    coach_id = fields.Many2one(
        'hr.employee', 'Coach', compute=False, readonly=False,
        domain=False,
        help='Select the "Employee" who is the coach of this employee.\n'
             'The "Coach" has no specific rights or responsibilities by default.')

class HolidaysAllocation(models.Model):

    _inherit = "hr.leave.allocation"


    
    # def action_approve(self):
    #     if self.employee_id.user_id == self.env.user:
    #         raise UserError(_("You cannot approve your own time-off"))

    #     if self.env.user.id not in self.employee_id.approver_time_off_ids.ids:
    #         raise UserError(_("You don't have access to approve time-off from this employee ("+self.employee_id.name+")."))
    #     result = super(HolidaysAllocation, self).action_approve()
    #     return result

    # def action_refuse(self):
    #     if self.employee_id.user_id == self.env.user:
    #         raise UserError(_("You cannot refuse your own time-off"))

    #     if self.env.user.id not in self.employee_id.approver_time_off_ids.ids:
    #         raise UserError(_("You don't have access to reject time-off from this employee ("+self.employee_id.name+")."))
    #     result = super(HolidaysAllocation, self).action_refuse()
    #     return result

    # def add_follower(self, employee_id):
    #     employee = self.env['hr.employee'].browse(employee_id)
    #     if employee.user_id:
    #         self.message_subscribe(partner_ids=employee.user_id.partner_id.ids)
    #     if employee.coach_id and employee.coach_id.user_id.partner_id and employee.coach_id.user_id.partner_id.id not in self.message_partner_ids.ids:
    #         self.message_subscribe(partner_ids=employee.coach_id.user_id.partner_id.ids)
    #     if employee.approver_time_off_ids:
    #         for appr in employee.approver_time_off_ids:
    #             if appr.partner_id and  appr.partner_id.id not in self.message_partner_ids.ids:
    #                 self.message_subscribe(partner_ids=appr.partner_id.ids)


class HolidaysRequest(models.Model):

    _inherit = "hr.leave"

    message_approval = fields.Char("Message Aproval")
    message_approved = fields.Char("Message Approved")
    message_rejected = fields.Char("Message Rejected")

    def action_approve_warning(self, approver):
        if not self.is_manager and self.employee_id.department_id.is_included_in_timeoff_approval and self.employee_id.department_id.manager_id.user_id == self.env.user:
            pass
        else:
            super(HolidaysRequest, self).action_approve_warning(approver)

    @api.constrains('state', 'number_of_days', 'holiday_status_id')
    def _check_holidays(self):
        if self.env.user.has_group('odes_hr2_custom.group_see_all_record_hr'):
            pass
        else:
            super(HolidaysRequest, self)._check_holidays()

    @api.constrains('date_from', 'date_to', 'hr_year_id')
    def _check_current_year_leave_req(self):
        """
        Override the method is used to validate only current year leave request.
 
        @param self : Object Pointer
        @return : True or False
        ------------------------------------------------------
        """
        pass

    # def unlink(self):
    #     for data in self:
    #         message = _(
    #                 'Leave %(leave_type)s requested from %(name)s already deleted.',
    #                 leave_type=data.holiday_status_id.display_name,
    #                 name=data.employee_id.name
    #             )
    #         data.employee_id.message_post(body=message,partner_ids=data.message_partner_ids.ids)
    #     return super(HolidaysRequest, self).unlink()

    # def _check_approval_update(self, state):
    #     """ Check if target state is achievable. """
    #     if self.env.is_superuser():
    #         return

    #     current_employee = self.env.user.employee_id
    #     is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
    #     is_manager = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')

    #     for holiday in self:
    #         val_type = holiday.validation_type

    #         if state == 'confirm' or state == 'draft':
    #             if current_employee == holiday.employee_id:
    #                 return

    #         if not is_manager and state != 'confirm':
    #             if state == 'draft':
    #                 if holiday.state == 'refuse':
    #                     raise UserError(_('Only a Time Off Manager can reset a refused leave.'))
    #                 if holiday.date_from and holiday.date_from.date() <= fields.Date.today():
    #                     raise UserError(_('Only a Time Off Manager can reset a started leave.'))
    #                 if holiday.employee_id != current_employee:
    #                     raise UserError(_('Only a Time Off Manager can reset other people leaves.'))

    #             else:
    #                 if val_type == 'no_validation' and current_employee == holiday.employee_id:
    #                     continue
    #                 # use ir.rule based first access check: department, members, ... (see security.xml)
    #                 holiday.check_access_rule('write')

    #                 # This handles states validate1 validate and refuse
    #                 if holiday.employee_id == current_employee:
    #                     raise UserError(_('Only a Time Off Manager can approve/refuse its own requests.'))

    #                 if (state == 'validate1' and val_type == 'both') or (state == 'validate' and val_type == 'manager') and holiday.holiday_type == 'employee':
    #                     if not is_officer and self.env.user != holiday.employee_id.leave_manager_id:
    #                         raise UserError(_('You must be either %s\'s manager or Time off Manager to approve this leave') % (holiday.employee_id.name))

    @api.model_create_multi
    def create(self, vals_list):
        result = super(HolidaysRequest, self).create(vals_list)

        for data in result:
            data.approver_id = data.employee_id.leave_manager_id.id
        #     holiday = data
        #     message = _(
        #             'Leave %(leave_type)s planned on %(date)s waiting for approval.',
        #             leave_type=holiday.holiday_status_id.display_name,
        #             date=holiday.date_from
        #         )
        #     if data.message_approval:
        #         message = data.message_approval
        #     holiday.message_post(
        #         body=message,partner_ids=holiday.message_partner_ids.ids)
        return result

    # def add_follower(self, employee_id):
    #     employee = self.env['hr.employee'].browse(employee_id)
    #     if employee.user_id:
    #         self.message_subscribe(partner_ids=employee.user_id.partner_id.ids)
    #     if employee.coach_id and employee.coach_id.user_id.partner_id and employee.coach_id.user_id.partner_id.id not in self.message_partner_ids.ids:
    #         self.message_subscribe(partner_ids=employee.coach_id.user_id.partner_id.ids)
    #     if employee.approver_time_off_ids:
    #         for appr in employee.approver_time_off_ids:
    #             if appr.partner_id and  appr.partner_id.id not in self.message_partner_ids.ids:
    #                 self.message_subscribe(partner_ids=appr.partner_id.ids)


    def action_approve(self):        
        if self.employee_id.user_id == self.env.user:
            raise UserError(_("You cannot approve your own time-off"))

        date_now = datetime.now()
        if self.approver_id == self.env.user:
            self.write({'state': 'validate', 'date_approve': date_now})
            self.activity_update()
        elif self.env.user in self.approver_id.substitute_approver_ids:
            self.write({'state': 'validate', 'date_approve': date_now})
            self.activity_update()
        else:
            raise UserError("Request can only be approved by approver and it's substitutes")

    def activity_update(self):
        super(HolidaysRequest, self).activity_update()

        for holiday in self:
            if holiday.state == 'confirm':
                approver = holiday.approver_id or  holiday.sudo()._get_responsible_for_approval() or self.env.user
                print (approver, "=== approver")
                for substitute in approver.substitute_approver_ids:
                    self.activity_schedule(
                    'hr_expense.mail_act_leave_approval',
                    note= "Substitute Approver for this Leave Request",
                    user_id=substitute.id)
    
                        

    #     if self.env.user.id not in self.employee_id.approver_time_off_ids.ids:
    #         raise UserError(_("You don't have access to approve time-off from this employee ("+self.employee_id.name+")."))
    #     # if validation_type == 'both': this method is the first approval approval
    #     # if validation_type != 'both': this method calls action_validate() below
    #     if any(holiday.state != 'confirm' for holiday in self):
    #         raise UserError(_('Time off request must be confirmed ("To Approve") in order to approve it.'))

    #     current_employee = self.env.user.employee_id
    #     self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})


    #     # Post a second message, more verbose than the tracking message
    #     for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):
    #         message = _(
    #                 'Your %(leave_type)s planned on %(date)s has been accepted',
    #                 leave_type=holiday.holiday_status_id.display_name,
    #                 date=holiday.date_from
    #             )
    #         if holiday.message_approved:
    #             message = holiday.message_approved
    #         holiday.message_post(
    #             body=message,
    #             partner_ids=holiday.employee_id.user_id.partner_id.ids)

    #     self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
    #     if not self.env.context.get('leave_fast_create'):
    #         self.activity_update()
        # return True

    # def action_refuse(self):
    #     if self.employee_id.user_id == self.env.user:
    #         raise UserError(_("You cannot refuse your own time-off"))
    #     if self.env.user.id not in self.employee_id.approver_time_off_ids.ids:
    #         raise UserError(_("You don't have access to reject time-off from this employee ("+self.employee_id.name+")."))
    #     current_employee = self.env.user.employee_id
    #     if any(holiday.state not in ['draft', 'confirm', 'validate', 'validate1'] for holiday in self):
    #         raise UserError(_('Time off request must be confirmed or validated in order to refuse it.'))

    #     validated_holidays = self.filtered(lambda hol: hol.state == 'validate1')
    #     validated_holidays.write({'state': 'refuse', 'first_approver_id': current_employee.id})
    #     (self - validated_holidays).write({'state': 'refuse', 'second_approver_id': current_employee.id})
    #     # Delete the meeting
    #     self.mapped('meeting_id').unlink()
    #     # If a category that created several holidays, cancel all related
    #     linked_requests = self.mapped('linked_request_ids')
    #     if linked_requests:
    #         linked_requests.action_refuse()

    #     # Post a second message, more verbose than the tracking message
    #     for holiday in self:
    #         if holiday.employee_id.user_id:
    #             message = _('Your %(leave_type)s planned on %(date)s has been refused', leave_type=holiday.holiday_status_id.display_name, date=holiday.date_from)
    #             if holiday.message_rejected:
    #                 message = holiday.message_rejected

    #             holiday.message_post(
    #                 body=message,
    #                 partner_ids=holiday.employee_id.user_id.partner_id.ids)

    #     self._remove_resource_leave()
    #     self.activity_update()
    #     return True

    # @api.returns('mail.message', lambda value: value.id)
    # def message_post(self, *,
    #                  body='', subject=None, message_type='notification',
    #                  email_from=None, author_id=None, parent_id=False,
    #                  subtype_xmlid=None, subtype_id=False, partner_ids=None, channel_ids=None,
    #                  attachments=None, attachment_ids=None,
    #                  add_sign=True, record_name=False,
    #                  **kwargs):
    #     holiday = self
    #     if len(holiday) == 1:
    #         if holiday.message_approved and body == _('Your %(leave_type)s planned on %(date)s has been accepted',leave_type=holiday.holiday_status_id.display_name,date=holiday.date_from):
    #             body = holiday.message_approved
    #         if holiday.message_rejected and body == __('Your %(leave_type)s planned on %(date)s has been refused', leave_type=holiday.holiday_status_id.display_name, date=holiday.date_from):
    #             body = holiday.message_rejected

    #     result = super(HolidaysRequest, self).message_post(
    #                      body=body, subject=subject, message_type=message_type,
    #                      email_from=email_from, author_id=author_id, parent_id=parent_id,
    #                      subtype_xmlid=subtype_xmlid, subtype_id=subtype_id, partner_ids=partner_ids, channel_ids=channel_ids,
    #                      attachments=None, attachment_ids=None,
    #                      add_sign=add_sign, record_name=record_name,
    #                      kwargs=kwargs)

    #     return result

    @api.constrains('state', 'number_of_days', 'holiday_status_id')
    def _check_holidays(self):
        if not self.env.user.has_group('odes_hr2_custom.group_see_all_record_hr'):
            return super(HolidaysRequest, self)._check_holidays()


class HrExpenseSheet(models.Model):

    _inherit = "hr.expense.sheet"

    sgd_currency_id = fields.Many2one('res.currency', string='SGD Currency', readonly=True, default=lambda self: self.env.ref('base.SGD'))
    total_amount_curr = fields.Monetary('Total Amount SGD', currency_field='sgd_currency_id', compute='_compute_amount', store=True, tracking=True)
    company_tax_amount = fields.Monetary('Taxes Amount', currency_field='currency_id', compute='_compute_amount', store=True, tracking=True)
    sgd_tax_amount = fields.Monetary('Taxes Amount SGD', currency_field='sgd_currency_id', compute='_compute_amount', store=True, tracking=True)
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')

    # @api.model
    # def create(self, vals):
    #     result = super(HrExpenseSheet, self).create(vals)
    #     for data in result:
    #         if data.employee_id.approver_expense_ids:
    #             for appr in data.employee_id.approver_expense_ids:
    #                 if appr.partner_id and  appr.partner_id.id not in data.message_partner_ids.ids:
    #                     data.message_subscribe(partner_ids=appr.partner_id.ids)
    #     return result
    
    def approve_expense_sheets(self):
        if self.employee_id.user_id == self.env.user:
            raise UserError(_("You cannot approve your own expenses"))

        # if self.env.user.id not in self.employee_id.approver_expense_ids.ids:
        #     raise UserError(_("You don't have access to approve expense from this employee ("+self.employee_id.name+")."))
        # result = super(HrExpenseSheet, self).approve_expense_sheets()
        # return result        

        date_now = datetime.now()
        if self.user_id == self.env.user:
            self.write({'state': 'approve', 'expense_approved_dates': date_now})
            self.activity_update()
        elif self.env.user in self.user_id.substitute_approver_ids:
            self.write({'state': 'approve', 'expense_approved_dates': date_now})
            self.activity_update()
        else:
            raise UserError("Request can only be approved by approver and it's substitutes") 

    def activity_update(self):
        super(HrExpenseSheet, self).activity_update()

        for expense_report in self.filtered(lambda hol: hol.state == 'submit'):
            for substitute in expense_report.user_id.substitute_approver_ids:                
                self.activity_schedule(
                'hr_expense.mail_act_expense_approval',
                user_id=substitute.id)

    # def refuse_sheet(self, reason):
    #     if self.employee_id.user_id == self.env.user:
    #         raise UserError(_("You cannot refuse your own expenses"))

    #     if self.env.user.id not in self.employee_id.approver_expense_ids.ids:
    #         raise UserError(_("You don't have access to reject expense from this employee ("+self.employee_id.name+")."))
    #     result = super(HrExpenseSheet, self).refuse_sheet(reason)
    #     return result

    # @api.depends('expense_line_ids.tax_ids','expense_line_ids.total_amount_company','expense_line_ids.total_amount')
    # def _compute_amount(self):
    #     for sheet in self:
    #         sheet.total_amount = sum(sheet.expense_line_ids.mapped('total_amount_company'))
    #         sheet.total_amount_curr = sum(sheet.expense_line_ids.mapped('total_amount'))
    #         sgd_tax_amount = 0
    #         company_tax_amount = 0
    #         for expense in sheet.expense_line_ids:
    #             sgd_tax = expense.total_amount - expense.untaxed_amount
    #             sgd_tax_amount+= sgd_tax
    #             company_tax_amount += expense.currency_id._convert(
    #                 sgd_tax, sheet.currency_id,
    #                 sheet.company_id, expense.date or fields.Date.today())
    #         sheet.sgd_tax_amount = sgd_tax_amount
    #         sheet.company_tax_amount = company_tax_amount

    # def _compute_attachment_number(self):
    #     for sheet in self:
    #         attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'hr.expense.sheet'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
    #         attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
    #         attachment_number = sum(sheet.expense_line_ids.mapped('attachment_number'))
    #         attachment_number=attachment.get(sheet.id, 0)
    #         sheet.attachment_number = attachment_number

    # def action_get_attachment_view(self):
    #     attach_obj = self.env['ir.attachment']
    #     check1 = attach_obj.sudo().search([('res_model', '=', 'hr.expense'), ('res_id', 'in', self.expense_line_ids.ids)])
    #     check2 = attach_obj.sudo().search([('res_model', '=', 'hr.expense.sheet'), ('res_id', 'in', self.ids)])
    #     res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
    #     domain_ids = check1.ids + check2.ids
    #     res['domain']= [('id','in',domain_ids)]
    #     res['context'] = {
    #         'default_res_model': 'hr.expense.sheet',
    #         'default_res_id': self.id,
    #         'create': False,
    #         'edit': False,
    #     }
    #     return res


class HrHolidaysStatus(models.Model):
    _inherit = "hr.leave.type"


    # def name_get(self):
    #     if self._context.get('employee_id'):
    #         result = []
    #         for data in self:
    #             name = data.name2 or data.name
    #             result.append((data.id, name))
    #     else:
    #         result = super(HrHolidaysStatus, self).name_get()

    #     return result


class ApolloHrExpenseLineSettings(models.Model):
    _name = "apollo.hr.expense.line.settings"
    _description = "Apollo HR Expense Line Settings"

    name = fields.Char("Name")
    account_id = fields.Many2one("account.account",'Account')
    company_id = fields.Many2one("res.company",'Company')


    # @api.onchange('company_id')
    # def _onchange_expense_line(self):
    #     for expense in self:
    #         expense.account_id = False


class ApolloHrExpenseLine(models.Model):
    _name = "apollo.hr.expense.line"
    _description = "Apollo HR Expense Line"


    product_id = fields.Many2one('product.product', string='Product',  domain="[('can_be_expensed', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure',  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    unit_price = fields.Float("Unit Price")
    quantity = fields.Float(required=True, digits='Product Unit of Measure', default=1)
    tax_ids = fields.Many2many('account.tax', 'expense_tax_line', 'expense_line_id', 'tax_id',
        domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'purchase')]", string='Taxes',readonly=False)
    subtotal = fields.Float("Total", digits='Account')
    expense_id = fields.Many2one("hr.expense","Expense")
    company_id = fields.Many2one("res.company","Company",related="expense_id.company_id")
    name = fields.Char("Description")
    expense_settings_id = fields.Many2one("apollo.hr.expense.line.settings","Expense Type")

    # @api.onchange('product_id', 'company_id')
    # def _onchange_expense_line(self):
    #     for expense in self:
    #         if expense.product_id:
    #             exp = expense.expense_id
    #             if not exp.date:
    #                 raise UserError(_('Please set expense date first.'))
    #             if not exp.currency_id:
    #                 raise UserError(_('Please set expense currency first.'))
    #             standard_price = expense.product_id.price_compute('standard_price')[expense.product_id.id]
    #             unit_amount = exp.company_id.currency_id._convert(standard_price, exp.currency_id, exp.company_id,exp.date)
    #             expense.unit_price = unit_amount
    #             expense.name = expense.product_id.name
    #             expense.product_uom_id = expense.product_id.uom_id
    #             expense.tax_ids = expense.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == expense.company_id)  # taxes only from the same company

    # @api.onchange('quantity', 'unit_price', 'tax_ids', 'currency_id')
    # def _onchange_amount(self):
    #     for expense in self:
    #         exp = expense.expense_id
    #         if not exp.currency_id:
    #             raise UserError(_('Please set expense currency first.'))
    #         if not exp.employee_id:
    #             raise UserError(_('Please set expense employee first.'))

    #         taxes = expense.tax_ids.compute_all(expense.unit_price, exp.currency_id, expense.quantity, expense.product_id, exp.employee_id.user_id.partner_id)
    #         expense.subtotal = taxes.get('total_included')

    
class HrExpense(models.Model):

    _inherit = "hr.expense"

    line_expense_ids = fields.One2many("apollo.hr.expense.line","expense_id","Lines")
    total_amount = fields.Monetary("Total", compute='_compute_amount', store=True, currency_field='currency_id', tracking=True)
    total_amount_company = fields.Monetary("Total (Company Currency)", compute='_compute_total_amount_company', store=True, currency_field='company_currency_id')
    expense_settings_id = fields.Many2one("apollo.hr.expense.line.settings","Expense Type")
    # def action_submit_expenses(self):
    #     result = super(HrExpense, self).action_submit_expenses()
    #     if self.employee_id.user_id.partner_id:
    #         if self.employee_id.user_id.partner_id.id not in self.message_partner_ids.ids:
    #             self.message_subscribe([self.employee_id.user_id.partner_id.id])
    #     if self.env.user.partner_id:
    #         if self.env.user.partner_id.id not in self.message_partner_ids.ids:
    #             self.message_subscribe([self.env.user.partner_id.id])
    #     body = """<p><b>Expense """+self.name+""" for employee """+self.employee_id.name+"""</b></p><p style="margin-top:10px;">Already approved.</p>
    #     """
    #     partner_ids = self.message_partner_ids.ids
    #     self.message_post(body=body,partner_ids=partner_ids,subject="Expense Approved")
    #     return result

    # @api.onchange('name')
    # def _onchange_predict_product(self):
    #     d = 1

    # @api.onchange('expense_settings_id')
    # def _onchange_expense_settings_id(self):
    #     for expense in self:
    #         if expense.expense_settings_id.account_id:
    #             expense.account_id = expense.expense_settings_id.account_id.id

    # @api.depends('quantity', 'unit_amount', 'tax_ids', 'currency_id')
    # def _compute_amount(self):
    #     for expense in self:
    #         expense.untaxed_amount = expense.unit_amount * expense.quantity
    #         taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id, expense.employee_id.user_id.partner_id)
    #         expense.total_amount = taxes.get('total_included')

    # @api.depends('date', 'total_amount', 'company_currency_id','line_expense_ids')
    # def _compute_total_amount_company(self):
    #     for expense in self:
    #         amount = 0
    #         for line in expense.line_expense_ids:
    #             amount+=line.subtotal
    #         date_expense = expense.date
    #         expense.total_amount_company = expense.currency_id._convert(
    #                 expense.total_amount, expense.company_currency_id,
    #                 expense.company_id, date_expense or fields.Date.today())

    # @api.model
    # def default_get(self, fields):
    #     result = super(HrExpense, self).default_get(fields)
    #     result['currency_id'] = self.env.ref('base.SGD').id
    #     return result

    # @api.model
    # def create(self, vals):
    #     result = super(HrExpense, self).create(vals)
    #     for data in result:
    #         data.product_id = data.company_id.def_exp_product_id.id or False
    #     return result




class Contract(models.Model):
    _inherit = 'hr.contract'


    currency_id = fields.Many2one("res.currency",string="Currency",related=False, readonly=True,compute='_compute_currency_id')


    def _compute_currency_id(self):
        for data in self:
            data.currency_id = self.env.ref('base.SGD').id



class Employee(models.Model):
    _inherit = 'hr.employee'

    approver_time_off_ids = fields.Many2many("res.users", "approver_time_off_rel", "user_id", "emp_id", "Approver Time off")
    approver_expense_ids = fields.Many2many("res.users", "approver_expense_rel", "user_id", "emp_id", "Approver Expense")
    allocation_used_display = fields.Char(compute='_compute_total_allocation_used')
    allocation_used_count = fields.Float('Total number of days off used', compute='_compute_total_allocation_used')
    allocation_display = fields.Char(compute='_compute_allocation_count')
    allocation_count = fields.Float('Total number of days allocated.', compute='_compute_allocation_count')
    initial_name = fields.Char("Initial Name")
    substitute_approver_ids = fields.Many2many(related="user_id.substitute_approver_ids", readonly=False)

    
    # def _compute_allocation_count(self):
    #     data = self.env['hr.leave.allocation'].read_group([
    #         ('employee_id', 'in', self.ids),
    #         ('holiday_status_id.active', '=', True),
    #         ('state', '=', 'validate'),'|',('end_date','>=',fields.Datetime.now()),('end_date','=',False)
    #     ], ['number_of_days:sum', 'employee_id'], ['employee_id'])
    #     rg_results = dict((d['employee_id'][0], d['number_of_days']) for d in data)
    #     for employee in self:
    #         employee.allocation_count = rg_results.get(employee.id, 0.0)
    #         employee.allocation_display = "%g" % employee.allocation_count

    # def _compute_total_allocation_used(self):
    #     data = self.env['hr.leave'].read_group([
    #         ('employee_id', 'in', self.ids),
    #         ('holiday_status_id.active', '=', True),
    #         ('state', '=', 'validate'),
    #     ], ['number_of_days:sum', 'employee_id'], ['employee_id'])
    #     rg_results = dict((d['employee_id'][0], d['number_of_days']) for d in data)

    #     for employee in self:
    #         employee.allocation_used_count = rg_results.get(employee.id, 0.0)
    #         employee.allocation_used_display = "%g" % employee.allocation_used_count

    # def get_current_mont(self):
    #     hr_month = date.today().month
    #     return hr_month

    # def get_total_leave_year(self,leave_type):
    #     result = 0
    #     leave_allo_obj = self.env['hr.leave.allocation']
    #     hr_year = date.today().year
    #     leaves_allo = leave_allo_obj.search([('carry_forward','=',False),('state','=','validate'),('employee_id','=',self.id),('hr_year_id.name','=',hr_year),('holiday_status_id','=',leave_type.id)])
    #     for l in leaves_allo:
    #         result+=l.number_of_days_display
    #     return result

    # def get_cary_over_leave_year(self,leave_type):
    #     result = 0
    #     leave_allo_obj = self.env['hr.leave.allocation']
    #     hr_year = date.today().year
    #     leaves_allo = leave_allo_obj.search([('carry_forward','=',True),('state','=','validate'),('employee_id','=',self.id),('hr_year_id.name','=',hr_year),('holiday_status_id','=',leave_type.id)])
    #     for l in leaves_allo:
    #         result+=l.number_of_days_display
    #     return result


    # def get_total_leave_pending(self,leave_type):
    #     result = 0
    #     leave_obj = self.env['hr.leave']
    #     hr_year = date.today().year
    #     leaves = leave_obj.search([('state','not in',['refuse','cancel','validate']),('employee_id','=',self.id),('hr_year_id.name','=',hr_year),('holiday_status_id','=',leave_type.id)])
    #     for l in leaves:
    #         result+=l.number_of_days
    #     return result

    # def get_total_leave_taken(self,leave_type):
    #     result = 0
    #     leave_obj = self.env['hr.leave']
    #     hr_year = date.today().year
    #     leaves = leave_obj.search([('state','in',['validate']),('employee_id','=',self.id),('hr_year_id.name','=',hr_year),('holiday_status_id','=',leave_type.id)])
    #     for l in leaves:
    #         result+=l.number_of_days
    #     return result


    # def get_alloc_all_leave(self):
    #     hr_year = date.today().year
    #     leave_allo_obj = self.env['hr.leave.allocation']
    #     hr_type_obj = self.env['hr.leave.type']
    #     hr_types = hr_type_obj
    #     get_leaves_allo = leave_allo_obj.search([('state','=','validate'),('employee_id','=',self.id),('hr_year_id.name','=',hr_year)])
    #     for gla in get_leaves_allo:
    #         if gla.holiday_status_id not in hr_types:
    #             hr_types += gla.holiday_status_id
    #     return hr_types



    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     """Name Search."""
    #     if self._context.get('open_all_employee'):
    #         result = self.sudo().search([('company_id','in',[False,self.env.company.id])])
    #         result = result.name_get()
    #     else:
    #         result = super(Employee, self).name_search(name,args,operator,limit)

    #     return result



    # @api.onchange('coach_id')
    # def onchange_coach_id_manager(self):
    #     for emp in self:
    #         if emp.coach_id:
    #             emp.leave_manager = emp.coach_id.id
    #             emp.parent_id = emp.coach_id.id
