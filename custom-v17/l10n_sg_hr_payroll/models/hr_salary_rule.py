# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    def _get_parent(self):
        return self.env.ref('payroll.structure_base', False)

    parent_id = fields.Many2one(
        'hr.payroll.structure', string='Parent', default=_get_parent)

    def _get_parent_structure(self):
        parent = self.mapped('parent_id')
        if parent:
            parent = parent._get_parent_structure()
        return parent + self

    def get_all_rules(self):
        """
        @return: returns a list of tuple (id, sequence) of rules that are maybe to apply
        """
        all_rules = []
        for struct in self:
            all_rules += struct.rule_ids._recursive_search_of_rules()
        return all_rules
