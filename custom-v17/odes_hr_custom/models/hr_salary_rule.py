# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class HrSalaryRuleCategory(models.Model):
    _inherit = 'hr.salary.rule.category'

    def _sum_salary_rule_category(self, localdict, amount):
        self.ensure_one()
        if self.parent_id:
            localdict = self.parent_id._sum_salary_rule_category(localdict, amount)
        localdict['categories'].dict[self.code] = localdict['categories'].dict.get(self.code, 0) + amount
        return localdict