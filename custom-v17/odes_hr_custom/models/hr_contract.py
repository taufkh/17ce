# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.models import MAGIC_COLUMNS
from odoo.fields import Date
from odoo.exceptions import ValidationError
from odoo.tools import html_sanitize

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    is_origin_contract_template = fields.Boolean(compute='_compute_is_origin_contract_template', string='Is origin contract a contract template ?', readonly=True)

    def _compute_is_origin_contract_template(self):
        for contract in self:
            origin_contract = getattr(contract, 'origin_contract_id', False)
            contract.is_origin_contract_template = bool(origin_contract and not origin_contract.employee_id)
