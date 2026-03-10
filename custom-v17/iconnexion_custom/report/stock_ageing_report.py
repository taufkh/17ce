# -*- coding: utf-8 -*-


from datetime import datetime, timedelta
from odoo import models, api,fields
from odoo.tools import pycompat, DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_round


# class StockAgingReport(models.AbstractModel):
# 	_inherit = 'report.stock_ageing_report_app.report_stockaginginfo' 
# 	_description = 'Stock Aging Report'


# 	def _get_warehouse_details(self, data, warehouse):
# 		lines =[]
# 		if warehouse:
# 			start_date_data = data.get('start_date')
# 			category_ids = data.get('category_ids')
# 			filter_type = data.get('filter_type')
# 			product_ids = data.get('product_ids')
# 			company  = data.get('company_id')
# 			if filter_type == 'category':
# 				product_ids = self.env['product.product'].search([('categ_id', 'in', category_ids.ids)])
# 			elif filter_type == 'product':
# 				product_ids = self.env['product.product'].search([('id', 'in', product_ids.ids)])
# 			else:
# 				product_ids = self.env['product.product'].search([])
# 			product_data = []
# 			for product_id  in product_ids:
# 				value = {}
# 				counter = 1
# 				col = "col_"
# 				if product_id.product_template_attribute_value_ids:
# 					variant = product_id.product_template_attribute_value_ids._get_combination_name()
# 					name = variant and "%s (%s)" % (product_id.name, variant) or product_id.name
# 					product_name = name
# 				else:
# 					product_name = product_id.name
# 				value.update({
# 					'product_id'         : product_id.id,
# 					'product_name'       : product_name or '',
# 					'product_code'       : product_id.default_code or '',
# 					'cost_price'         : product_id.standard_price  or 0.00,
# 				})
# 				is_last = False
# 				for date_data in self._get_date_data(data):
# 					if counter == 6:
# 						is_last = True
# 					start_date = date_data.get('start_date')
# 					end_date = date_data.get('end_date')
# 					warehouse_id = warehouse.id
# 					company_id = company.id
# 					delivered_qty = self._get_product_info(product_id.id, warehouse_id, start_date, end_date, 'customer', 'outgoing', 'Delivery Orders', is_last, company_id)
# 					received_qty = self._get_product_in_info(product_id.id, warehouse_id, start_date, end_date, 'internal', 'incoming', 'Receipts', is_last, company_id)
# 					return_in_qty = self._get_return_in_qty(product_id.id, warehouse_id, start_date, end_date, 'outgoing','Delivery Orders', is_last, company_id)
# 					return_out_qty = self._get_return_out_qty(product_id.id, warehouse_id, start_date, end_date, 'incoming','Receipts', is_last, company_id)
# 					adjusted_qty = self._get_adjusted_qty(product_id.id, warehouse_id, start_date, end_date, is_last, company_id)
# 					qty_on_hand = (received_qty + adjusted_qty + return_in_qty) - (delivered_qty - return_out_qty)
# 					qty_hand_key = col + str(counter)
# 					value.update({ qty_hand_key : qty_on_hand })
# 					counter += 1
# 				product_data.append(value)
# 			lines.append({'product_data':product_data})
# 		return lines



# 	def _get_location_details(self, data, location):
# 		lines =[]
# 		if location:
# 			start_date_data = data.get('start_date')
# 			category_ids = data.get('category_ids')
# 			filter_type = data.get('filter_type')
# 			product_ids = data.get('product_ids')
# 			company  = data.get('company_id')
# 			if filter_type == 'category':
# 				product_ids = self.env['product.product'].search([('categ_id', 'in', category_ids.ids)])
# 			elif filter_type == 'product':
# 				product_ids = self.env['product.product'].search([('id', 'in', product_ids.ids)])
# 			else:
# 				product_ids = self.env['product.product'].search([])
# 			product_data = []
# 			for product_id  in product_ids:
# 				value = {}
# 				counter = 1
# 				col = "col_"
# 				if product_id.product_template_attribute_value_ids:
# 					variant = product_id.product_template_attribute_value_ids._get_combination_name()
# 					name = variant and "%s (%s)" % (product_id.name, variant) or product_id.name
# 					product_name = name
# 				else:
# 					product_name = product_id.name
# 				value.update({
# 					'product_id'         : product_id.id,
# 					'product_name'       : product_name or '',
# 					'product_code'       : product_id.default_code or '',
# 					'cost_price'         : product_id.standard_price  or 0.00,
# 				})
# 				is_last = False
# 				for date_data in self._get_date_data(data):
# 					if counter == 6:
# 						is_last = True
# 					start_date = date_data.get('start_date')
# 					end_date = date_data.get('end_date')
# 					company_id = company.id
# 					location_id = location.id
# 					delivered_qty = self._get_product_location_info(product_id.id, start_date, end_date, is_last, location_id, company_id)
# 					received_qty = self._get_product_location_in_info(product_id.id, start_date, end_date, is_last, location_id, company_id)
# 					return_in_qty = self._get_return_location_in_qty(product_id.id, start_date, end_date, is_last, location_id, company_id)
# 					return_out_qty = self._get_return_location_out_qty(product_id.id, start_date, end_date, is_last, location_id, company_id)
# 					adjusted_qty = self._get_adjusted_location_qty(product_id.id, start_date, end_date, is_last, location_id, company_id)
# 					qty_on_hand = (received_qty + adjusted_qty + return_in_qty) - (delivered_qty - return_out_qty)
# 					qty_hand_key = col + str(counter)
# 					value.update({ qty_hand_key : qty_on_hand })
# 					counter += 1
# 				product_data.append(value)
# 			lines.append({'product_data':product_data})
# 		return lines

