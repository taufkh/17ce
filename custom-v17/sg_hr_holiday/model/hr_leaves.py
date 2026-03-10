from datetime import date, datetime

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DSDF
from odoo.tools.float_utils import float_round


class HrHolidays(models.Model):
    _inherit = "hr.leave"

    start_date = fields.Datetime(
        'Starting Date', default=datetime.strftime(date.today(), '%Y-01-01'))
    end_date = fields.Datetime(
        'Ending Date', default=datetime.strftime(date.today(), '%Y-12-31'))
    notes = fields.Text('Reasons', readonly=False)
    state = fields.Selection(selection_add=[
        ('draft', 'New'), ('confirm', 'Waiting Pre-Approval'),
        ('refuse', 'Refused'), ('validate1', 'Waiting Final Approval'),
        ('validate', 'Approved'), ('cancel', 'Cancelled')], string='State',
        readonly=True, help='The state is set to \'Draft\', when a \
        holiday request is created.\nThe state is \'Waiting Approval\', when \
        holiday request is confirmed by user.\nThe state is \'Refused\', when \
        holiday request is refused by manager.\nThe state is \'Approved\', \
        when holiday request is approved by manager.')
    rejection = fields.Text('Reason')
    create_date = fields.Datetime('Create Date', readonly=True)
    write_date = fields.Datetime('Write Date', readonly=True)
    day = fields.Char(string='Day')
    carry_forward = fields.Boolean('Carry Forward Leave')

    _sql_constraints = [
        ('type_value',
         "CHECK((holiday_type='employee' AND employee_id IS NOT NULL) or "
         "(holiday_type='company' AND mode_company_id IS NOT NULL) or "
         "(holiday_type='category' AND category_id IS NOT NULL) or "
         "(holiday_type='department' AND department_id IS NOT NULL) )",
         "The employee, department, company or employee category of this\
         request is missing. Please make sure that your user login is linked\
         to an employee."),
        ('date_check2', "CHECK ((date_from <= date_to))", "The start date must\
        be anterior to the end date."),
        ('duration_check', "CHECK ( number_of_days >= 0 )", "If you want to\
        change the number of days you should use the 'period' mode"),
    ]


class HrHolidaysStatus(models.Model):
    _inherit = "hr.leave.type"

    cry_frd_leave = fields.Float('Carry Forward Leave',
                                 help='Maximum number of Leaves to be \
                                 carry forwarded!')
    name2 = fields.Char('Leave Type')
    default_leave_allocation = fields.Integer('Default Leave Allocation',
                                              default=0)
    expiry_period = fields.Integer("Expiry Period(In Months)", default=12)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """Name Search."""
        if not args:
            args = []
        hr_holiday_rec = self.search(['|', ('code', operator, name),
                                      ('name', operator, name)
                                      ] + args, limit=limit)
        return hr_holiday_rec.name_get()

    def name_get(self):
        if not self._context.get('employee_id'):
            # leave counts is based on employee_id, would be inaccurate if not based on correct employee
            return super(HrHolidaysStatus, self).name_get()
        res = []
        for record in self:
            name = record.name2 or record.name
            if record.allocation_type != 'no':

                virtual_remaining_leaves = float_round(record.virtual_remaining_leaves, precision_digits=2) or 0.0
                max_leaves = float_round(record.max_leaves, precision_digits=2) or 0.0

                if not max_leaves:
                    virtual_remaining_leaves = 0.0

                name = "%(name)s (%(count)s)" % {
                    'name': name,
                    'count': _('%g remaining out of %g') % (virtual_remaining_leaves, max_leaves
                                                            ) + (_(' hours') if record.request_unit == 'hour' else _(' days'))
                }
            res.append((record.id, name))
        return res


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    employee_leave_ids = fields.One2many(
        'hr.leave', 'employee_id', 'Leaves', copy=False)
