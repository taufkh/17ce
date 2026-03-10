# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleReport(models.Model):
	_inherit = "sale.report"

	product_brand_id = fields.Many2one('product.brand', 'Brand', readonly=True)

	def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
		fields['brand_id'] = ", t.product_brand_id as product_brand_id"
		groupby += ', t.product_brand_id'
		return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

	#     fields['warehouse_id'] = ", s.warehouse_id as warehouse_id"
	#     groupby += ', s.warehouse_id'
	#     return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)