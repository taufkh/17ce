# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountInvoiceReport(models.Model):
	_inherit = 'account.invoice.report'

	product_brand_id = fields.Many2one('product.brand', 'Brand', readonly=True)

	def _select(self):
		return super(AccountInvoiceReport, self)._select() + ", template.product_brand_id as product_brand_id"