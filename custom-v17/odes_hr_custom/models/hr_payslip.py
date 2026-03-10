# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.odes_hr_custom.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips, ResultRules

import pytz
import math
import time
import calendar
from dateutil import parser, rrule
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import odoo.tools as tools
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DSDTF,\
    DEFAULT_SERVER_DATE_FORMAT as DSDF


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_localdict(self):
        self.ensure_one()
        worked_days_dict = {line.code: line for line in self.worked_days_line_ids if line.code}
        inputs_dict = {line.code: line for line in self.input_line_ids if line.code}

        employee = self.employee_id
        contract = self.contract_id

        localdict = {
            **self._get_base_local_dict(),
            **{
                'categories': BrowsableObject(employee.id, {}, self.env),
                'rules': BrowsableObject(employee.id, {}, self.env),
                'payslip': Payslips(employee.id, self, self.env),
                'worked_days': WorkedDays(employee.id, worked_days_dict, self.env),
                'inputs': InputLine(employee.id, inputs_dict, self.env),
                'employee': employee,
                'contract': contract,
                'result_rules': ResultRules(employee.id, {}, self.env)
            }
        }
        return localdict


    # @api.model
    # def get_inputs(self, contracts, date_from, date_to):
    #     res = []

    #     structure_ids = contracts.get_all_structures()
    #     rule_ids = self.env['hr.payroll.structure'].browse(
    #         structure_ids).get_all_rules()
    #     sorted_rule_ids = [id for id, sequence in sorted(
    #         rule_ids, key=lambda x:x[1])]
    #     inputs = self.env['hr.salary.rule'].browse(
    #         sorted_rule_ids).mapped('input_ids')

    #     input_codes_list = []

    #     for contract in contracts:
    #         for input in inputs:
    #             input_codes_list.append(input.code)

    #     hr_payslip_input_type = self.env['hr.payslip.input.type'].search([('code','in',input_codes_list)])

    #     for input in hr_payslip_input_type:
    #         input_data = {
    #             'input_type_id': input.id
    #         }
    #         res += [input_data]

    #     return res


    # @api.model
    # def get_worked_day_lines(self, contract_ids, date_from, date_to):
    #     """Get worked day lines.

    #     @param contract_ids: list of contract id
    #     @return: returns a list of dict containing the input that should be
    #     applied for the given contract between date_from and date_to
    #     """
    #     def local_2_utc(str_date):
    #         if str_date:
    #             timez = 'Singapore'
    #             if self._context and 'tz' in self._context and \
    #                     self._context.get('tz') is not False:
    #                 timez = self._context.get('tz')
    #             local_tz = pytz.timezone(timez)
    #             datetime_without_tz = datetime.strptime(str(str_date), DSDTF)
    #             datetime_with_tz = local_tz.localize(
    #                 datetime_without_tz, is_dst=None)
    #             #  time
    #             datetime_in_utc = datetime_with_tz.astimezone(pytz.utc)
    #         return datetime_in_utc

    #     def was_on_leave(employee_id, datetime_day):
    #         holiday_obj = self.env['hr.leave']
    #         res1 = {'name': False, 'days': 0.0, 'half_work': False}

    #         #  day = datetime_day.strftime("%Y-%m-%d")
    #         day_fr = datetime_day.replace(hour=0, minute=0, second=0)
    #         day_fr = local_2_utc(day_fr.strftime(DSDTF))
    #         day_to = datetime_day.replace(hour=23, minute=59, second=59)
    #         day_to = local_2_utc(day_to.strftime(DSDTF))
    #         domain = [('state', '=', 'validate'),
    #                   ('employee_id', '=', employee_id),
    #                   ('request_date_from', '<=', day_to.strftime(DSDTF)),
    #                   ('request_date_to', '>=', day_fr.strftime(DSDTF))]
    #         holiday_ids = holiday_obj.search(domain)
    #         if holiday_ids:
    #             diff_day = holiday_obj._check_holiday_to_from_dates(
    #                 datetime_day, datetime_day, holiday_ids[0].employee_id.id)
    #             res = holiday_ids[0].holiday_status_id.name
    #             res1['name'] = res
    #             num_days = diff_day
    #             if holiday_ids[0].request_unit_half:
    #                 num_days = 0.5
    #                 res1['half_work'] = True
    #             res1['days'] = num_days
    #         return res1

    #     res = []
    #     for contract in contract_ids:
    #         if not contract.resource_calendar_id:
    #             #  fill only if the contract as a working schedule linked
    #             continue
    #         work_entry_type = self.env.ref(
    #             'l10n_sg_hr_payroll.hr_work_entry_type_total_normal_working_days_paid_at')
    #         attendances = {
    #             'sequence': 1,
    #             'work_entry_type_id': work_entry_type.id,
    #             'number_of_days': 0.0,
    #             'number_of_hours': 0.0,
    #             'contract_id': contract.id,
    #         }
    #         leaves = {}
    #         day_from = datetime.strptime(str(date_from), "%Y-%m-%d")

    #         day_to = datetime.strptime(str(date_to), "%Y-%m-%d")

    #         nb_of_days = (day_to - day_from).days + 1
    #         d1 = datetime.strptime(str(date_from) + ' 00:00:00', DSDTF)
    #         d2 = datetime.strptime(str(date_from) + ' 23:59:59', DSDTF)
    #         resource_obj = self.env['resource.resource']
    #         resource_id = resource_obj.search([('user_id', '=',
    #                                             self.employee_id.user_id.id)],
    #                                           limit=1)
    #         for day in range(0, nb_of_days):
    #             calendar_id = contract.resource_calendar_id
    #             working_hours_on_day = calendar_id.get_work_hours_count(
    #                 d1 + timedelta(days=day), d2 + timedelta(days=day),
    #                 resource_id.id)
    #             if working_hours_on_day:
    #                 #  the employee had to work
    #                 leave_type = was_on_leave(
    #                     contract.employee_id.id, day_from +
    #                     timedelta(days=day))
    #                 if leave_type and leave_type['name']:
    #                     #  if he was on leave, fill the leaves dict
    #                     if leave_type['name'] in leaves:
    #                         leaves[leave_type['name']]['number_of_days'
    #                             ] += leave_type['days'].get('days')
    #                         leaves[leave_type['name']]['number_of_hours'
    #                             ] += leave_type['days'].get('hours')
    #                     else:
    #                         work_entry_type = self.env['hr.work.entry.type'].search([('code','=',leave_type['name'])], limit=1)

    #                         if not work_entry_type:
    #                             work_entry_type = self.env.ref('l10n_sg_hr_payroll.hr_work_entry_type_sick_leaves')

    #                         leaves[leave_type['name']] = {
    #                             'sequence': 5,
    #                             'work_entry_type_id': work_entry_type.id,
    #                             'code': leave_type['name'],
    #                             'number_of_days': leave_type['days'].get('days'),
    #                             'number_of_hours': leave_type['days'].get(
    #                                 'hours'),
    #                             'contract_id': contract.id,
    #                         }
    #                 else:
    #                     #  add the input vals to tmp (increment if existing)
    #                     from_date = datetime.fromtimestamp(time.mktime(
    #                         time.strptime(str(date_from), "%Y-%m-%d")))
    #                     curr_date = from_date + relativedelta(days=day)
    #                     curr_date = curr_date.date()
    #                     holiday_line_obj = self.env['hr.holiday.lines']
    #                     domain = [('holiday_id.state', '=', 'validated'),
    #                               ('holiday_date', '=', str(curr_date))]
    #                     public_holiday_ids = holiday_line_obj.search(domain)
    #                     if public_holiday_ids:
    #                         continue
    #                     else:
    #                         attendances['number_of_days'] += 1.0
    #                         attendances['number_of_hours'] += (
    #                             working_hours_on_day)
    #         leaves = [value for key, value in leaves.items()]
    #         res += [attendances] + leaves
    #     return res
