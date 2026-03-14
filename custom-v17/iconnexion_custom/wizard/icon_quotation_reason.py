from datetime import datetime, timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast


class IconQuotationReasonWizard(models.TransientModel):
	_name = "icon.quotation.reason.wizard"
	_description = "Quotation Reason Wizard"

	sale_id = fields.Many2one('sale.order', string='Sale Order', compute="_get_sale_id")
	sale_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
	reason = fields.Char('Reason')
	date = fields.Datetime('Date Input Reason',default=fields.Datetime.now())
	company_id = fields.Many2one('res.company', string='Company')

	def _get_sale_id(self):
		context = dict(self._context or {})
		active_model = context.get('active_model')
		active_id = context.get('active_id')
		self.sale_id = False
		if not active_model or not active_id:
			return
		if active_model == 'sale.order.line':            
			self.sale_line_id = active_id

	@api.model
	def default_get(self, fields):
		res = super(IconQuotationReasonWizard, self).default_get(fields)
		active_ids = self.env.context.get('active_ids', [])
		context = dict(self._context or {})
		active_id = context.get('active_id')
		res['sale_line_id'] = active_id
		
		return res

	def button_change_reason(self):
		partner_ids = []
		if self.sale_line_id.product_id.product_brand_id:
			for partner_id in self.sale_line_id.product_id.product_brand_id.icon_product_partner_manager_ids:
				partner_ids.append(partner_id.id)

		# for sm in self.env.company.icon_sales_manager_ids:			
		# 	partner_ids.append(sm.id)
		self.sale_line_id.write({
				'reason': self.reason,
				'is_request_margin': True,
				'date_input': fields.Datetime.now(),
				'request_user_id': self.env.uid,
				})
		
		self.sale_line_id.order_id.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
								'iconnexion_custom.so_request_low_margin',
							values={'sales': self.sale_line_id,},
							subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
							partner_ids=partner_ids,
							subject='Low Margin Request '+ self.sale_line_id.order_id.name,                            
					) 
		


		return True
			# return self.write_to_history()

	# def write_to_history(self):
	#     odes_stage_obj = self.env['odes.crm.stage']
	#     last_stage = odes_stage_obj.search([('lead_id', '=', self.lead_id.id)], order='start_datetime desc', limit=1)

	#     last_stage.write({
	#         'backward_reason':self.reason
	#         })

class IconQuotationApproveWizard(models.TransientModel):
	_name = "icon.quotation.approve.wizard"
	_description = "Quotation Approve Wizard"

	sale_id = fields.Many2one('sale.order', string='Sale Order', compute="_get_sale_id")
	sale_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
	reason = fields.Char('Reason')
	date = fields.Datetime('Date Request Lower Margin',default=fields.Datetime.now())
	approve_user_id = fields.Many2one('res.users',string='User Approve')
	request_user_id = fields.Many2one('res.users',string='User Request')

	@api.model
	def default_get(self, fields):
		res = super(IconQuotationApproveWizard, self).default_get(fields)
		active_ids = self.env.context.get('active_ids', [])
		context = dict(self._context or {})
		active_id = context.get('active_id')
		res['sale_line_id'] = active_id
		sale_line = self.env['sale.order.line'].browse(active_id)
		res['date'] = sale_line.date_input
		res['reason'] = sale_line.reason
		if sale_line.request_user_id:
			res['request_user_id'] = sale_line.request_user_id.id
		return res
	def _get_sale_id(self):
		context = dict(self._context or {})
		active_model = context.get('active_model')
		active_id = context.get('active_id')
		self.sale_id = False
		if not active_model or not active_id:
			return
		if active_model == 'sale.order.line':
			
			self.sale_line_id = active_id

	def button_approve(self):
		partner_ids = []
		if self.sale_line_id.product_id.product_brand_id:
			for partner_id in self.sale_line_id.product_id.product_brand_id.icon_product_partner_manager_ids:
				partner_ids.append(partner_id.id)
				
		self.sale_line_id.order_id.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
								'iconnexion_custom.so_approve_low_margin',
							values={'sales': self.sale_line_id,},
							subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
							partner_ids=partner_ids,
							subject='Low Margin Approve '+ self.sale_line_id.order_id.name,                            
					)
		self.sale_line_id.write({
				'is_lower_margin': False,
				'is_request_margin': False,
				'date_approve': fields.Datetime.now(),
				'approve_user_id': self.env.uid,
				})
		return True
