# -*- coding: utf-8 -*- 
import re
import base64
import logging

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.http import request
from odoo.tools import partition, pycompat
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)



class ResCompany(models.Model):
    _inherit = 'res.company'

    company_reg_no = fields.Char("Company Reg No")
    gst_reg_no = fields.Char("GST Reg No")
    min_margin = fields.Float("Minimum Margin", default=15)
    icon_customer_service_ids = fields.Many2many('res.partner','cs_company_partner_rel','cs_company_id','partner_id', string="Customer Service")
    icon_finance_ids = fields.Many2many('res.partner','finance_company_partner_rel','finance_company_id','partner_id', string="Finance")
    icon_product_manager_ids = fields.Many2many('res.partner', 'product_company_partner_rel','product_company_id','partner_id', string="Product Manager")
    icon_sales_manager_ids = fields.Many2many('res.partner', 'sales_company_partner_rel','sales_company_id','partner_id', string="Sales Manager")
    #pi_debit_id = fields.Many2one('account.account','Debit')
    #pi_credit_id = fields.Many2one('account.account','Credit')
    #pi_invoice_debit_id = fields.Many2one('account.account','Debit')
    #pi_invoice_credit_id = fields.Many2one('account.account','Credit')

    pi_credit_account_id = fields.Many2one('account.account', string='Account Debit',required=False)
    property_product_pricelist = fields.Many2one('product.pricelist', string='Default Pricelist')