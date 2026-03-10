# -*- coding: utf-8 -*-
from operator import is_
from odoo import api, fields, models, _, tools, SUPERUSER_ID

from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.osv.expression import AND
from collections import defaultdict
# from datetime import datetime
from datetime import datetime, timedelta
from odoo.tools import float_is_zero
from dateutil.relativedelta import relativedelta,FR,WE
from odoo.tools.misc import formatLang, get_lang
from functools import partial
from operator import itemgetter
from itertools import groupby


class SaleOrder(models.Model):
	_inherit = "sale.order"


	design_owner_id = fields.Many2one('res.users', string='Design Owner', compute='_compute_design_owner_lead')
	freight_terms_id = fields.Many2one('delivery.carrier', string='Freight Terms Method')
	is_odes = fields.Boolean(string="Odes Company", compute='compute_is_odes', store=True)
	pi_payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ], string='PI Payment Status', readonly=True, copy=False, index=True, tracking=3, default='not_paid')
	is_request_margin = fields.Boolean('Request Lower Margin', compute='_compute_is_request_margin', store=True)
	user_confirm_id = fields.Many2one('res.users', string='User Confirm')
	cpn = fields.Char(string='CPN', compute='_compute_cpn', store=True, readonly=True)

	def taxes(self):
		datas = []
		dot = []
		for i in self.order_line:
			datas.append({
				'tax':i.tax_id.amount,
				'amount': i.price_subtotal,
				'dump': 'dump',
			})
		grouper = itemgetter("tax", "dump")
		for key, grp in groupby(sorted(datas, key = grouper), grouper):
			temp_dict = dict(zip(["tax","dump"], key))
			amount = 0
			for item in grp:
				amount += item["amount"]
			temp_dict["amount"] = amount
			dot.append(temp_dict)

		return dot

	@api.depends('order_line.name')
	def _compute_cpn(self):
		for record in self:
			record.cpn = ', '.join(order_line.name for order_line in record.order_line)

	@api.model_create_multi
	def create(self, values_list):
		if self.user_has_groups('iconnexion_mccoy_custom.group_iconnexion_cannot_create_quo_wo_opportunity'):
			for values in values_list:
				if not values.get('opportunity_id'):
					raise ValidationError("Cannot create quotation without opportunity.")
		return super(SaleOrder, self).create(values_list)

	def button_quote_crm(self):
		context = dict(self.env.context or {})
		# looping dan create
		list_order_line = []
		date_now = fields.Datetime.now()
		for sale in self:
			if len(sale.order_line) > 1:
				raise ValidationError("You have product in Quotation Before, please remove it")

			
			if sale.opportunity_id:
				if sale.opportunity_id.annual_qty <= 0:
					raise UserError(_("Please enter the annual quantity in the pipeline."))
				if (sale.opportunity_id.stage_id.name == 'Proposal' or sale.opportunity_id.stage_id.name == 'New') and sale.opportunity_id.is_iconnexion:
					proposal_stage_id = self.env['crm.stage'].search([('name','=','Quotation')])
					if proposal_stage_id:
						sale.opportunity_id.with_context({'icon_view': 1,}).write({'stage_id': proposal_stage_id.id})

				for part in sale.opportunity_id.odes_part_ids:
					if part.product_id:
						moqs = part.product_id.product_tmpl_id.moq_ids.filtered(lambda line: (line.product_variant_id==part.product_id or not line.product_variant_id) )
						moq_id = False
						r_code = 0
						moq = 0
						if part.no_of_per <= 0 and not sale.is_odes:
							raise UserError(_("No. of Per cannot be %s. Please enter a valid No. of Per for the pipeline item.") % part.no_of_per)
						if sale.opportunity_id.annual_qty <= 0 and not sale.is_odes:
							raise UserError(_("Annual Qty cannot be %s. Please enter a valid Annual Qty for the pipeline item.") % part.no_of_per)
						quantity = sale.opportunity_id.annual_qty *  part.no_of_per if sale.opportunity_id.annual_qty and part.no_of_per else 1
						# if sale.opportunity_id.annual_qty and part.no_of_per:
						# 	quantity = sale.opportunity_id.annual_qty *  part.no_of_per
						spq = part.product_id.product_tmpl_id.qty_multiply
						if moqs:
							moq = moqs[0].min_qty
							r_code = moqs[0].r_code
							moq_id = moqs[0].id
						sale_delay = (int(part.product_id.custom_lead_time_by_weeks) * 7 )
						list_order_line.append((0, 0, {'name':part.product_id.name,
													'product_id':part.product_id.id,
													'quote_price_unit':part.quoted_price,
													'price_unit':part.quoted_price,
													'icon_sale_price' : part.product_id.product_tmpl_id.list_price,
													'product_uom_qty': quantity,
													'customer_lead': part.product_id.custom_lead_time_by_weeks or 0,
													'sale_delay': part.product_id.custom_lead_time_by_weeks or 0,
													# 'customer_request_date':  date_now + relativedelta(days=sale_delay or 0.0,weekday=FR),
													'icpo_request_deliver_date':  date_now + relativedelta(days=(sale_delay or 0.0 -7),weekday=WE(-1)) ,#1 week before customer request date on wed
													'committed_date': date_now + relativedelta(days=sale_delay or 0.0,weekday=FR),
													'moq_id': moq_id,
													'ar_code': r_code,
													'r_code': r_code,
													'a_moq': moq,
													'moq': moq,
													'spq': spq, 'a_spq': spq
													}))
			sale.write({'order_line':list_order_line })
		return True

	@api.depends('order_line.is_request_margin')
	def _compute_is_request_margin(self):
		for sale in self:
			request_margin = any(line.is_request_margin for line in sale.order_line)
			sale.is_request_margin = request_margin
	

	@api.depends('company_id')
	def compute_is_odes(self):
		for sale in self:
			company_name = sale.company_id.name
			if company_name and 'odes' in company_name.lower():
				sale.is_odes = True
			else:
				sale.is_odes = False


	def copy(self, default=None):
		if default is None:
			default = {}
		if not isinstance(default, dict):
			default = dict(default)
		res = super(SaleOrder, self).copy(default)
		res.message_post(body='This Quotation was duplicated from %s' % (self.name))
		return res


	def _compute_design_owner_lead(self):
		for sale in self:
			sale.design_owner_id = sale.opportunity_id.design_owner_id


	def action_confirm(self):
		for line in self.order_line:
			today_datetime = datetime.now()
			lead_time = line.sale_delay
			weekday = 4  # Friday (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
			
			days_until_friday = (weekday - today_datetime.weekday()) % 7
			days_to_add = (lead_time * 7) + days_until_friday
			committed_date = today_datetime + timedelta(days=days_to_add)
			line.committed_date = committed_date
		res = super(SaleOrder, self).action_confirm()
		for sale in self:
			if not (sale.bill_to_contact_person or sale.bill_to_street or sale.bill_to_block or sale.bill_to_city or sale.bill_to_state or sale.bill_to_zip or sale.bill_to_country_id or sale.bill_to_remarks):
				raise ValidationError("Please check the bill-to address!")
			if not (sale.ship_to_contact_person or sale.ship_to_street or sale.ship_to_block or sale.ship_to_city or sale.ship_to_state or sale.ship_to_zip or sale.ship_to_country_id or sale.ship_to_remarks):
				raise ValidationError("Please check the ship-to address!")
			if not sale.payment_term_id:
				raise ValidationError("Please check the payment terms!")
			if not sale.freight_terms_id and (sale.is_iconnexion or sale.is_mccoy) and sale.quotation_type == 'item':
				raise ValidationError("Please check the freight terms!")
			if not sale.opportunity_id and (sale.is_iconnexion or sale.is_mccoy)  and sale.quotation_type == 'item':
				raise ValidationError("Please check the opportunity field!")
			for line in sale.order_line:
				if len(line.tax_id) == 0:
					raise UserError(_("Tax cannot be empty. Users should choose the zero-rated tax option instead."))
				if not line.customer_request_date and (sale.is_iconnexion or sale.is_mccoy) and sale.quotation_type == 'item':
					raise ValidationError("Please provide a customer request date.")
			sale.user_confirm_id = self.env.user.id
		return res
	
	@api.onchange('partner_id')
	def onchange_partner_id(self):
		res = super(SaleOrder, self).onchange_partner_id()
		self._onchange_opportunity()
		self.freight_terms_id = self.partner_id.freight_terms_id
		self.carrier_id = self.partner_id.property_delivery_carrier_id
		return res
	
	
	def _prepare_invoice(self):
		invoice_vals = super(SaleOrder, self)._prepare_invoice()
		invoice_vals['delivery_method_id'] = self.carrier_id.id
		invoice_vals['freight_terms_id'] = self.freight_terms_id.id
		return invoice_vals
	
	def print_icon_quotation(self):
		if self.opportunity_id:				
			if self.opportunity_id.stage_id.name == 'Quotation' and self.opportunity_id.is_iconnexion:
				proposal_stage_id = self.env['crm.stage'].search([('name','=','DIP')])
				if proposal_stage_id:
					self.opportunity_id.with_context({'icon_view': 1,}).write({'stage_id': proposal_stage_id.id})
		if self.is_iconnexion:
			return self.env.ref('iconnexion_custom.report_quotation_mccoy').report_action(self)
		if not self.is_iconnexion and not self.is_odes:
			return self.env.ref('odes_custom.report_sale_order').report_action(self)
	
				   

class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"

	buffer_stock_ids = fields.Many2many(
        'buffer.stock.line', 
        string='Buffer Link', 
        compute='_compute_buffer_stock_ids',
    )
	invoice_date = fields.Date(related="order_id.invoice_ids.invoice_date", string="Invoice Date", store=True)
	committed_date = fields.Datetime('Committed Date', copy=True,
									  help="This is the delivery date promised to the customer. "
										   "If set, the delivery order will be scheduled based on "
										   "this date rather than product lead times.", tracking=True)
	contact_id = fields.Many2one('res.partner','Contact', related='order_id.contact_id', store=True)

	@api.onchange('customer_request_date')
	def _onchange_customer_request_date(self):
		if self.customer_request_date:
			two_weeks_from_today = datetime.now().date() + timedelta(days=15)
			if self.customer_request_date > datetime.now().date() and self.customer_request_date <= two_weeks_from_today:
				# If the customer request date is before today, set the deliver date to next Wednesday
				days_until_wednesday = (2 - datetime.now().date().weekday()) % 7
				if days_until_wednesday == 0:
					days_until_wednesday = 7
				self.icpo_request_deliver_date = datetime.now().date() + timedelta(days=days_until_wednesday)
			else:
				# Calculate the Wednesday two weeks before the customer request date
				days_until_wednesday = (2 - self.customer_request_date.weekday()) % 7
				if days_until_wednesday == 0:
					days_until_wednesday = 7
				wednesday_two_weeks_before = self.customer_request_date - timedelta(weeks=2)
				while wednesday_two_weeks_before.weekday() != 2:
					wednesday_two_weeks_before -= timedelta(days=1)
				self.icpo_request_deliver_date = wednesday_two_weeks_before

		else:
			# If there is no customer request date, set the deliver date to today
			self.icpo_request_deliver_date = datetime.now().date()

	def name_get(self):
		res = []
		for record in self:
			name = '%s - %s) %s' % (record.order_id.name ,record.serial_numbers, record.name)
			res.append((record.id, name))
		return res

	def _compute_buffer_stock_ids(self):
		for line in self:
			line.buffer_stock_ids = self.env['buffer.stock.line'].search([
                ('sale_order_line_id', '=', line.id)
            ])

	@api.depends('quote_price_unit', 'product_id', 'product_id.seller_ids.customer_id', 'order_id.partner_id' )
	def _compute_is_special_price(self):
		for product in self:
			product.is_special_price = False
			if product.product_id.seller_ids:
				for sup in product.product_id.seller_ids:
					if sup.customer_id.id == product.order_id.partner_id.id:
						product.is_special_price = True
						break
					else:
						product.is_special_price = False

	def _get_configured_main_company(self):
		param_env = self.env['ir.config_parameter'].sudo()
		company_ref = (param_env.get_param('iconnexion_mccoy_custom.main_company_ref') or 'base.main_company').strip()
		company = False
		if company_ref.isdigit():
			company = self.env['res.company'].browse(int(company_ref))
		else:
			company = self.env.ref(company_ref, raise_if_not_found=False)
		return company if company and company.exists() else self.env.company

	@api.onchange('product_id')
	def product_id_change(self):
		#moq ambil yang paling kecil
		# di order dilimit Orders must be made in multiples of the SPQ
		# custom_lead_time_by_weeks > ganti customerlead
		
		res = super(SaleOrderLine, self).product_id_change()
		if self.company_id != self._get_configured_main_company():
			vals = {}
			domain = [('product_id','=',self.product_id.id),('order_partner_id','=',self.order_partner_id.id)]
			if self._origin.id:
				domain = AND([domain, [('id','!=',self._origin.id)]])
			if self.product_id and self.order_partner_id:
				product = self.product_id.with_context(
					lang=get_lang(self.env, self.order_id.partner_id.lang).code,
					partner=self.order_id.partner_id,
					quantity=vals.get('product_uom_qty') or self.product_uom_qty,
					date=self.order_id.date_order,
					pricelist=self.order_id.pricelist_id.id,
					uom=self.product_uom.id
				)
				date_now = fields.Datetime.now()
				sale_delay = (int(self.product_id.custom_lead_time_by_weeks) * 7 )
				vals['committed_date'] = date_now + relativedelta(days=sale_delay or 0.0,weekday=FR)
				# vals['customer_request_date'] = date_now + relativedelta(days=self.product_id.sale_delay or 0.0,weekday=FR)
				vals['sale_delay'] = self.product_id.custom_lead_time_by_weeks
				order_line = self.search(domain, limit=1)
				# vals['moq'] = self.product_id.moq
				vals['a_spq']=vals['spq'] = self.product_id.product_tmpl_id.qty_multiply
				vals['icon_sale_price'] = self.product_id.product_tmpl_id.list_price
				if self.product_id.product_tmpl_id.product_brand_id:
					vals['brand'] = self.product_id.product_tmpl_id.product_brand_id.name
				# vals['moq'] = 
				moqs = self.product_id.product_tmpl_id.moq_ids.filtered(lambda line: (line.product_variant_id==self.product_id or not line.product_variant_id) )
				# vals['moq'] = moqs = self.product_tmpl_id.moq_ids.filtered(lambda line: (line.product_variant_id==self.product_id or not line.product_variant_id) and line.min_qty<=qty)
				if self.order_id.pricelist_id and self.order_id.partner_id:
					vals['quote_price_unit'] = vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
					vals['icon_sale_price'] = vals['quote_price_unit']

				if moqs:
					vals['a_moq'] = vals['moq'] = moqs[0].min_qty
					vals['ar_code'] =vals['r_code'] = moqs[0].r_code
					vals['moq_id'] = moqs[0].id
					# vals['quote_price_unit'] = moqs[0].price_unit 
				if product.seller_ids:
					for sup in product.seller_ids:
						if sup.customer_id.id == self.order_id.partner_id.id:	
							print('dddddddddddddddd', sup)						
							vals['quote_price_unit'] = sup.sale_price
							vals['icon_sale_price']= sup.sale_price
							vals['price_unit']= sup.sale_price
							
							vals['product_uom_qty'] = sup.min_qty
							if sup.moq != 0:
								vals['moq'] = sup.moq
							if sup.moq == 0 and moqs:
								vals['a_moq'] = vals['moq'] = moqs[0].min_qty
							if sup.delay != 0:
								vals['sale_delay'] = sup.delay
							if sup.product_name:
								vals['name'] = sup.product_name


			self.update(vals)
		return res

	@api.onchange('product_uom',)
	def product_uom_change(self):
		res = super(SaleOrderLine, self).product_uom_change()
		if self.company_id != self._get_configured_main_company():
			vals = {}
			domain = [('product_id','=',self.product_id.id),('order_partner_id','=',self.order_partner_id.id)]
			if self._origin.id:
				domain = AND([domain, [('id','!=',self._origin.id)]])
			if self.product_id and self.order_partner_id:
				product = self.product_id.with_context(
					lang=get_lang(self.env, self.order_id.partner_id.lang).code,
					partner=self.order_id.partner_id,
					quantity=vals.get('product_uom_qty') or self.product_uom_qty,
					date=self.order_id.date_order,
					pricelist=self.order_id.pricelist_id.id,
					uom=self.product_uom.id
				)
				moqs = self.product_id.product_tmpl_id.moq_ids.filtered(lambda line: (line.product_variant_id==self.product_id or not line.product_variant_id) )
				# moqs = self.product_id.product_tmpl_id.moq_ids.filtered(lambda line: (line.product_variant_id==self.product_id or not line.product_variant_id) and line.min_qty<=self.product_uom_qty).sorted(key=lambda r: r.min_qty,reverse=True)
				if self.order_id.pricelist_id and self.order_id.partner_id:
					vals['quote_price_unit'] = vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
					vals['icon_sale_price'] = vals['quote_price_unit']
				# vals['quote_price_unit'] = self.product_id.product_tmpl_id.list_price * ( 1 + (self.company_id.min_margin * 0.01 )+0.01)
				# if self.company_id.min_margin < 100:
				# 	vals['quote_price_unit'] = self.product_id.product_tmpl_id.list_price / ( 1 - ((self.company_id.min_margin+1) * 0.01) )

				# vals['price_unit'] =  vals['quote_price_unit']#self.product_id.product_tmpl_id.list_price
				# vals['icon_sale_price'] =  self.product_id.product_tmpl_id.list_price
				if moqs:
					# vals['icon_sale_price'] = moqs[0].price_unit
					vals['a_moq'] = moqs[0].min_qty
					vals['ar_code'] =vals['r_code'] = moqs[0].r_code
					vals['moq_id'] = moqs[0].id
					# vals['quote_price_unit'] = moqs[0].price_unit 

				if product.seller_ids:
					for sup in product.seller_ids:
						if sup.customer_id.id == self.order_id.partner_id.id:
							print('ssssssssssssss', sup)							
							vals['quote_price_unit'] = sup.sale_price
							vals['icon_sale_price']= sup.sale_price
							vals['price_unit']= sup.sale_price
							
							vals['product_uom_qty'] = sup.min_qty
							if sup.moq != 0:
								vals['moq'] = sup.moq
							if sup.moq == 0 and moqs:
								vals['a_moq'] = vals['moq'] = moqs[0].min_qty
							if sup.delay != 0:
								vals['sale_delay'] = sup.delay
							if sup.product_name:
								vals['name'] = sup.product_name

				# order_line = self.search(domain, limit=1)
				# if order_line:
				#     vals['quote_price_unit'] = order_line.price_unit
				# else:
				#     vals['quote_price_unit'] = vals['icon_sale_price']
			# vals['price_unit'] = 0
					  
			self.update(vals)
		return res

	@api.onchange('quote_price_unit', 'product_uom_qty')
	def product_quote_change(self):       
		#context not from change
		# if from onchange, using def write
		# gunakan def write , karena kalau pakai onchange user tidak bisa input harga sama sekali
		
		context = self._context
		vals = {} 
		order_line = self.env['sale.order.line'].search([('product_id', '=', self.product_id.id), ('quote_price_unit', '=', self.quote_price_unit), ('is_lower_margin', '=', False), ('order_id.partner_id', '=', self.order_id.partner_id.id)])
		if self.quote_price_unit:
			vals['price_unit'] = self.quote_price_unit

		if self.product_id and self.order_partner_id: 
			if self.is_iconnexion:
				margin = self.company_id.min_margin * 0.01
				s_margin2 = round(self.s_margin,3)
				if self.is_special_price:
					
					if s_margin2 != 0:
						vals['is_lower_margin'] = True
					else:
						vals['is_lower_margin'] = False
				else: 
					if s_margin2 < margin:
						if order_line:
							vals['is_lower_margin'] = False
						else:
							vals['is_lower_margin'] = True
					else:
						vals['is_lower_margin']= False

					if self.product_id.product_tmpl_id.list_price == 0:
						vals['is_lower_margin'] = True

				# if self.s_margin < margin and not self.order_id.is_lower_margin:
					# print ('sukses'*10)
					# raise ValidationError(_('Need management approval why salesman request for lower margin'))
					# raise ValidationError(_('Need management approval why salesman request for lower margin'))
					# can't save when margin under 15 persen
				# if link ke so , dan status quotation . ubah . 
				if self.order_id.opportunity_id:
					crm_parts = self.env['odes.part'].search([('lead_id','=',self.order_id.opportunity_id.id),('product_id','=',self.product_id.id
						)],limit=1)					
					crm_parts.with_context({'default_type': 'opportunity',}).write({'quoted_price':self.quote_price_unit})

		self.update(vals)
