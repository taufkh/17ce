from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields


class HrSalaryRuleExt(models.Model):
    _inherit = 'hr.salary.rule'
    _description = 'Inherited to categorized Ordinary and Additional Wages \
                    at salary rule level.'

    is_cpf = fields.Selection([('no_cpf', 'No CPF'),
                               ('ow', 'OW'),
                               ('aw', 'AW')], 'Is CPF')


class HrPayslipExt(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Inherited for Ordinary and Additional Wages Integration \
                    with Pay slip Computation.'

    def _get_ow_aw(self):
        """
            This method compute current payslip ow and aw
            and previous payslip total aw and ow
        """
        for rec in self:
            rec.current_ow = 0
            rec.current_aw = 0
            rec.current_aw_ow = current_aw_ow = 0
            rec.all_aw_ow = all_aw_ow = 0
            rec.all_aw_ow_limit = False
            today = datetime.today().date()
            current_year = today.year
            current_year_start_date = str(current_year) + '-01-01' or ''
            date_from = rec.date_from
            previous_month_last_date = date_from - relativedelta(days=1)
            payslip_ids = rec.search([
                ('employee_id', '=', rec.employee_id.id),
                ('contract_id', '=', rec.contract_id.id),
                ('date_from', '>=', current_year_start_date),
                ('date_to', '<=', previous_month_last_date)])
            ow_ids = rec.line_ids.filtered(
                lambda x: x.salary_rule_id.is_cpf == 'ow')
            aw_ids = rec.line_ids.filtered(
                lambda x: x.salary_rule_id.is_cpf == 'aw')
            for owline in ow_ids:
                if owline.category_id.code == 'DED_INCL_CPF':
                    rec.current_ow -= owline.amount
                else:
                    rec.current_ow += owline.amount
            for awline in aw_ids:
                if owline.category_id.code == 'DED_INCL_CPF':
                    rec.current_aw -= awline.amount
                else:
                    rec.current_aw += awline.amount
            if rec.current_ow > 6000:
                rec.current_ow = 6000
            current_aw_ow = rec.current_ow + rec.current_aw
            rec.current_aw_ow = current_aw_ow
            for payslip in payslip_ids:
                all_aw_ow += payslip.current_aw_ow
                rec.all_aw_ow = all_aw_ow
            if rec.all_aw_ow > 102000:
                rec.all_aw_ow_limit = True

    current_ow = fields.Float(
        string="Current Payslip OW", compute='_get_ow_aw')
    current_aw = fields.Float(
        string="Current Payslip AW", compute='_get_ow_aw')
    current_aw_ow = fields.Float("Current AW OW", compute='_get_ow_aw')
    all_aw_ow = fields.Float("All AW OW", compute='_get_ow_aw')
    all_aw_ow_limit = fields.Boolean('All Aw Ow Limit', compute='_get_ow_aw')

    def _get_payslip_lines(self):
        """
            This method used to pass ow_total and aw_total
            which is used in compution of aw and ow rules
        """
        self.ensure_one()

        localdict = self.env.context.get('force_payslip_localdict', None)
        if localdict is None:
            localdict = self._get_localdict()

        rules_dict = localdict['rules'].dict
        result_rules_dict = localdict['result_rules'].dict

        blacklisted_rule_ids = self.env.context.get(
            'prevent_payslip_computation_line_ids', [])

        result = {}

        ow_brw = self.env['hr.salary.rule'].search([('is_cpf', '=', 'ow')])
        aw_brw = self.env['hr.salary.rule'].search([('is_cpf', '=', 'aw')])
        ow_ids = ow_brw.ids
        aw_ids = aw_brw.ids
        ow_total = aw_total = 0.0

        for rule in sorted(self.struct_id.rule_ids, key=lambda x: x.sequence):
            if rule.id in blacklisted_rule_ids:
                continue
            localdict['result'] = None
            localdict['result_qty'] = 1.0
            localdict['result_rate'] = 100
            localdict['ow_total'] = ow_total
            localdict['aw_total'] = aw_total
            if rule._satisfy_condition(localdict):
                amount, qty, rate = rule._compute_rule(localdict)

                if rule.id in ow_ids:
                    ow_total += float(qty) * amount * rate / 100
                    ow_ids.remove(rule.id)
                elif rule.id in aw_ids:
                    aw_total += float(qty) * amount * rate / 100
                    aw_ids.remove(rule.id)

                #check if there is already a rule computed with that code
                previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                #set/overwrite the amount computed for this rule in the localdict
                tot_rule = amount * qty * rate / 100.0
                localdict[rule.code] = tot_rule
                result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty}
                rules_dict[rule.code] = rule
                # sum the amount for its salary category
                localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
                # create/overwrite the rule in the temporary results
                result[rule.code] = {
                    'sequence': rule.sequence,
                    'code': rule.code,
                    'name': rule.with_context(lang=self.employee_id.sudo().address_home_id.lang).name,
                    'note': rule.note,
                    'salary_rule_id': rule.id,
                    'contract_id': localdict['contract'].id,
                    'employee_id': localdict['employee'].id,
                    'amount': amount,
                    'quantity': qty,
                    'rate': rate,
                    'slip_id': self.id,
                }
        return result.values()
