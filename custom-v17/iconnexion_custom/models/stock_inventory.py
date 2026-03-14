# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero

class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    icpo_no = fields.Char('PO Number', readonly=True, required=False)
    ic_cpn = fields.Char('CPN', readonly=True, required=False)
    ic_datecode = fields.Char('Date Code', readonly=True, required=False)
    ic_customer = fields.Char('Customer', readonly=True, required=False)