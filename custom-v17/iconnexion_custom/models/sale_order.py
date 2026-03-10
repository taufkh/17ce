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
from itertools import groupby

class SaleOrder(models.Model):

	_inherit = "sale.order"
	_order = "id"

	sale_order_line_analyze_ids = fields.One2many('sale.order.line', 'analyze_order_id')
	bank_charges = fields.Monetary('Bank Charges')
	reason = fields.Char('Reason')
	is_lower_margin = fields.Boolean('Approve Lower Margin',default=False)
	is_sale_view = fields.Boolean('Sale View',default=False)
	contact_id = fields.Many2one('res.partner','Contact')
	is_iconnexion = fields.Boolean(string="iConnexion Company", compute='compute_is_iconnexion', store=True)
	is_pi_clear  = fields.Boolean('PI Clear',default=False, copy=False)
	is_generate_proforma = fields.Boolean(string="TT Payment Terms", compute='compute_is_generate_proforma', store=True)
	is_generate_proforma_to_process = fields.Boolean(string="TT Payment Terms to Process", compute='compute_is_generate_proforma', store=True)
	is_generate_proforma_partial_before_delivery = fields.Boolean(string="TT Partial Before Delivery Payment Terms", compute='compute_is_generate_proforma', store=True)	
	is_generate_proforma_partial = fields.Boolean(string="TT Partial Payment Terms", compute='compute_is_generate_proforma', store=True)
	attachment_count = fields.Integer(string='PO Attachment Count', compute='_compute_count_attachment')
	attachment_ids = fields.Many2many('ir.attachment', string='Customer PO Attachment')
	state = fields.Selection(selection_add=[('quote_lock', 'Quotation Lock')])
	client_order_ref = fields.Char(string='Customer PO', copy=True)
	select_address = fields.Selection(selection=[('address_1', 'Address 1'), ('address_2', 'Address 2'), ('address_3', 'Address 3')], string='Select Address')
	bill_to_street = fields.Char('Bill to Street', compute='compute_bill_to_street')
	bill_to_block = fields.Char('',compute='compute_bill_to_street')
	bill_to_city = fields.Char('',compute='compute_bill_to_street')
	bill_to_state = fields.Char('',compute='compute_bill_to_street')
	bill_to_zip = fields.Char('',compute='compute_bill_to_street')
	bill_to_country_id = fields.Char('',compute='compute_bill_to_street')
	bill_to_remarks = fields.Char('',compute='compute_bill_to_street')
	bill_to_contact_person = fields.Many2one('res.partner', '',compute='compute_bill_to_street')
	ship_to_street = fields.Char('Ship To Address',compute='compute_ship_to_street')
	ship_to_block = fields.Char('',compute='compute_ship_to_street')
	ship_to_city = fields.Char('',compute='compute_ship_to_street')
	ship_to_state = fields.Char('',compute='compute_ship_to_street')
	ship_to_zip = fields.Char('',compute='compute_ship_to_street')
	ship_to_country_id = fields.Char('',compute='compute_ship_to_street')
	ship_to_remarks = fields.Char('',compute='compute_ship_to_street')
	ship_to_contact_person = fields.Many2one('res.partner', '',compute='compute_ship_to_street')
	is_proforma_invoice = fields.Boolean('Is Proforma Invoice', copy=False,default=False)
	is_proforma_invoice_sent = fields.Boolean('Proforma Invoice Sent', copy=False,default=False)
	proforma_number = fields.Char('Proforma Invoice Number')
	proforma_invoice_count = fields.Integer(string='Proforma Invoice', compute='_compute_proforma_invoice_count')
	proforma_invoice_count_so = fields.Integer(string='Proforma Invoice SO', compute='_compute_proforma_invoice_so_count')
	payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Terms', check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=True)
	invoice_address_selection = fields.Selection(selection=[('address_1', 'Address 1'), ('address_2', 'Address 2'), ('address_3', 'Address 3'), ('address_4', 'Address 4')], string='Invoice Address Option')
	delivery_address_selection = fields.Selection(selection=[('address_1', 'Address 1'), ('address_2', 'Address 2'), ('address_3', 'Address 3'), ('address_4', 'Address 4')], string='Delivery Address Option')



	@api.onchange('partner_id')
	def _onchange_partner_id(self):
		if self.user_has_groups('iconnexion_custom.group_iconnexion_cs') or self.user_has_groups('iconnexion_custom.group_iconnexion_icon_salesman'):
			return {'domain': {'payment_term_id': [('payment_term_type','in',['advance_to_process','advance_before_delivery', 'partial_before_delivery_term', 'partial_cod_term'])]}}
		else:
			return

	def _compute_proforma_invoice_count(self):
		for i in self:
			proforma_invoice = self.env['account.move'].search_count([('sale_order_id', '=', i.id), ('is_proforma_invoice', '=', True)])
			i.proforma_invoice_count = proforma_invoice

	@api.depends('order_line.invoice_lines')
	def _get_invoiced(self):
		# The invoice_ids are obtained thanks to the invoice lines of the SO
		# lines, and we also search for possible refunds created directly from
		# existing invoices. This is necessary since such a refund is not
		# directly linked to the SO.
		for order in self:
			invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund') and r.is_proforma_invoice == False)
			order.invoice_ids = invoices
			order.invoice_count = len(invoices)

	def _compute_proforma_invoice_so_count(self):
		for i in self:
			if i.is_generate_proforma_partial_before_delivery == True:
				i.proforma_invoice_count_so = 0
			else:
				i.proforma_invoice_count_so = i.quotation_sale_id.proforma_invoice_count


	def preview_pinvoice(self):
		action = self.env.ref('iconnexion_custom.proforma_invoice_view_action').read()[0]
		action['domain'] = [('sale_order_id', '=', self.id)]
		return action

		
	def preview_pinvoice_so(self):
		action = self.env.ref('iconnexion_custom.proforma_invoice_view_action').read()[0]
		action['domain'] = [('sale_order_id', '=', self.quotation_sale_id.id)]
		return action


	def button_get_pi_payment(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': 'PI Payment',
			'view_mode': 'tree,form',
			'res_model': 'account.payment',
			'domain': [('sale_id', '=', self.id)],
			'context': {'default_sale_id':self.id,
						'default_payment_type': 'inbound',
						'default_partner_type': 'customer',
						'default_partner_id': self.partner_id.id,
						'default_amount': self.amount_total,						
						'default_company_id': self.company_id.id or self.env.company.id,
						}
			}

	def button_get_pi_payment_partial(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': 'PI Payment',
			'view_mode': 'tree,form',
			'res_model': 'account.payment',
			'domain': [('sale_id', '=', self.id)],
			'context': {'default_sale_id':self.id,
						'default_payment_type': 'inbound',
						'default_partner_type': 'customer',
						'default_partner_id': self.partner_id.id,
						# 'default_amount': - self.amount_dep_paid,						
						'default_company_id': self.company_id.id or self.env.company.id,
						}
			}
			
	@api.onchange('amount_untaxed')
	def _onchange_revenue(self):
		if self.amount_untaxed:
			for rec in self:
				if self.amount_untaxed:
					rec.opportunity_id.currency_revenue = self.amount_untaxed



	@api.depends('invoice_address_selection', 'partner_id.bill_to_contact_person_id', 'partner_id.ship_to_contact_person_id', 'partner_id.bill_to_contact_person2_id', 'partner_id.ship_to_contact_person2_id', 'partner_id.bill_to_contact_person3_id', 'partner_id.ship_to_contact_person3_id')
	def compute_bill_to_street(self):
		for sale in self:
			if sale.partner_id:
				if sale.invoice_address_selection == 'address_1' and sale.partner_id:
					sale.bill_to_contact_person = sale.partner_id.bill_to_contact_person_id
					sale.bill_to_street = sale.partner_id.bill_to_street
					sale.bill_to_block = sale.partner_id.bill_to_block
					sale.bill_to_city = sale.partner_id.bill_to_city
					sale.bill_to_state = sale.partner_id.bill_to_state
					sale.bill_to_zip = sale.partner_id.bill_to_zip
					sale.bill_to_country_id = sale.partner_id.bill_to_country_id.name
					sale.bill_to_remarks = sale.partner_id.bill_to_remarks
				elif sale.invoice_address_selection == 'address_2' and sale.partner_id:
					sale.bill_to_contact_person = sale.partner_id.bill_to_contact_person2_id
					sale.bill_to_street = sale.partner_id.bill_to_street2
					sale.bill_to_block = sale.partner_id.bill_to_block2
					sale.bill_to_city = sale.partner_id.bill_to_city2
					sale.bill_to_state = sale.partner_id.bill_to_state2
					sale.bill_to_zip = sale.partner_id.bill_to_zip2
					sale.bill_to_country_id = sale.partner_id.bill_to_country2_id.name
					sale.bill_to_remarks = sale.partner_id.bill_to_remarks2
				elif sale.invoice_address_selection == 'address_3' and sale.partner_id:
					sale.bill_to_contact_person = sale.partner_id.bill_to_contact_person3_id
					sale.bill_to_street = sale.partner_id.bill_to_street3
					sale.bill_to_block = sale.partner_id.bill_to_block3
					sale.bill_to_city = sale.partner_id.bill_to_city3
					sale.bill_to_state = sale.partner_id.bill_to_state3
					sale.bill_to_zip = sale.partner_id.bill_to_zip3
					sale.bill_to_country_id = sale.partner_id.bill_to_country3_id.name
					sale.bill_to_remarks = sale.partner_id.bill_to_remarks3
				elif sale.invoice_address_selection == 'address_4' and sale.partner_id:
					sale.bill_to_contact_person = sale.partner_id.bill_to_contact_person4_id
					sale.bill_to_street = sale.partner_id.bill_to_street4
					sale.bill_to_block = sale.partner_id.bill_to_block4
					sale.bill_to_city = sale.partner_id.bill_to_city4
					sale.bill_to_state = sale.partner_id.bill_to_state4
					sale.bill_to_zip = sale.partner_id.bill_to_zip4
					sale.bill_to_country_id = sale.partner_id.bill_to_country4_id.name
					sale.bill_to_remarks = sale.partner_id.bill_to_remarks4
				else:
					sale.bill_to_contact_person = sale.partner_id.bill_to_contact_person_id
					sale.bill_to_street = sale.partner_id.bill_to_street
					sale.bill_to_block = sale.partner_id.bill_to_block
					sale.bill_to_city = sale.partner_id.bill_to_city
					sale.bill_to_state = sale.partner_id.bill_to_state
					sale.bill_to_zip = sale.partner_id.bill_to_zip
					sale.bill_to_country_id = sale.partner_id.bill_to_country_id.name
					sale.bill_to_remarks = sale.partner_id.bill_to_remarks
			else:
				sale.bill_to_street = False
				sale.bill_to_block = False
				sale.bill_to_city = False
				sale.bill_to_state = False
				sale.bill_to_zip = False
				sale.bill_to_country_id = False
				sale.bill_to_remarks = False
				sale.bill_to_contact_person = False
				
				

	@api.depends('delivery_address_selection', 'partner_id.bill_to_contact_person_id', 'partner_id.ship_to_contact_person_id', 'partner_id.bill_to_contact_person2_id', 'partner_id.ship_to_contact_person2_id', 'partner_id.bill_to_contact_person3_id', 'partner_id.ship_to_contact_person3_id')
	def compute_ship_to_street(self):
		for sale in self:
			if sale.partner_id:
				if sale.delivery_address_selection == 'address_1' and sale.partner_id:
					sale.ship_to_contact_person = sale.partner_id.ship_to_contact_person_id
					sale.ship_to_street = sale.partner_id.ship_to_street
					sale.ship_to_block = sale.partner_id.ship_to_block
					sale.ship_to_city = sale.partner_id.ship_to_city
					sale.ship_to_state = sale.partner_id.ship_to_state
					sale.ship_to_zip = sale.partner_id.ship_to_zip
					sale.ship_to_country_id = sale.partner_id.ship_to_country_id.name
					sale.ship_to_remarks = sale.partner_id.ship_to_remarks
				elif sale.delivery_address_selection == 'address_2' and sale.partner_id:
					sale.ship_to_contact_person = sale.partner_id.ship_to_contact_person2_id
					sale.ship_to_street = sale.partner_id.ship_to_street2
					sale.ship_to_block = sale.partner_id.ship_to_block2
					sale.ship_to_city = sale.partner_id.ship_to_city2
					sale.ship_to_state = sale.partner_id.ship_to_state2
					sale.ship_to_zip = sale.partner_id.ship_to_zip2
					sale.ship_to_country_id = sale.partner_id.ship_to_country2_id.name
					sale.ship_to_remarks = sale.partner_id.ship_to_remarks2
				elif sale.delivery_address_selection == 'address_3' and sale.partner_id:
					sale.ship_to_contact_person = sale.partner_id.ship_to_contact_person3_id
					sale.ship_to_street = sale.partner_id.ship_to_street3
					sale.ship_to_block = sale.partner_id.ship_to_block3
					sale.ship_to_city = sale.partner_id.ship_to_city3
					sale.ship_to_state = sale.partner_id.ship_to_state3
					sale.ship_to_zip = sale.partner_id.ship_to_zip3
					sale.ship_to_country_id = sale.partner_id.ship_to_country3_id.name
					sale.ship_to_remarks = sale.partner_id.ship_to_remarks3
				elif sale.delivery_address_selection == 'address_4' and sale.partner_id:
					sale.ship_to_contact_person = sale.partner_id.ship_to_contact_person4_id
					sale.ship_to_street = sale.partner_id.ship_to_street4
					sale.ship_to_block = sale.partner_id.ship_to_block4
					sale.ship_to_city = sale.partner_id.ship_to_city4
					sale.ship_to_state = sale.partner_id.ship_to_state4
					sale.ship_to_zip = sale.partner_id.ship_to_zip4
					sale.ship_to_country_id = sale.partner_id.ship_to_country4_id.name
					sale.ship_to_remarks = sale.partner_id.ship_to_remarks4
				else:
					sale.ship_to_contact_person = sale.partner_id.ship_to_contact_person_id
					sale.ship_to_street = sale.partner_id.ship_to_street
					sale.ship_to_block = sale.partner_id.ship_to_block
					sale.ship_to_city = sale.partner_id.ship_to_city
					sale.ship_to_state = sale.partner_id.ship_to_state
					sale.ship_to_zip = sale.partner_id.ship_to_zip
					sale.ship_to_country_id = sale.partner_id.ship_to_country_id.name
					sale.ship_to_remarks = sale.partner_id.ship_to_remarks
			else:
				sale.ship_to_street = False
				sale.ship_to_block = False
				sale.ship_to_city = False
				sale.ship_to_state = False
				sale.ship_to_zip = False
				sale.ship_to_country_id = False
				sale.ship_to_remarks = False
				sale.ship_to_contact_person = False

	@api.model
	def default_get(self, fields):
		vals = super(SaleOrder, self).default_get(fields)
		default_partner = self.env.context.get('default_partner_id')
		default_contact = self.env.context.get('default_contact_id')
		if default_partner:
			vals['partner_id'] = default_partner

		vals['contact_id'] = default_contact
		return vals


	@api.depends('company_id')
	def compute_is_iconnexion(self):
		for lead in self:
			company_name = lead.company_id.name
			if company_name and 'iconnexion' in company_name.lower():
				lead.is_iconnexion = True
			else:
				lead.is_iconnexion = False

	@api.depends('payment_term_id')
	def compute_is_generate_proforma(self):
		for sales in self:
			if sales.payment_term_id:
				sales.is_generate_proforma_to_process = False
				sales.is_generate_proforma = False
				sales.is_generate_proforma_partial_before_delivery = False
				sales.is_generate_proforma_partial = False
				payment_name = sales.payment_term_id.name
				if sales.payment_term_id.payment_term_type == 'advance_to_process':
					sales.is_generate_proforma_to_process = True
				if sales.payment_term_id.payment_term_type == 'advance_before_delivery':
					sales.is_generate_proforma = True
				if sales.payment_term_id.payment_term_type == 'partial_before_delivery_term':
					sales.is_generate_proforma_partial_before_delivery = True
				if sales.payment_term_id.payment_term_type == 'partial_cod_term':
					sales.is_generate_proforma_partial = True
				


	@api.onchange('opportunity_id')
	def _onchange_opportunity(self):
		pricelist_obj = self.env['product.pricelist']
		if self.opportunity_id and not self.is_iconnexion :
			pricelist = pricelist_obj.search([('currency_id', '=', self.opportunity_id.currency_id.id)], limit=1)
			if pricelist:
				self.pricelist_id = pricelist.id

	@api.model
	def search(self, args, offset=0, limit=None, order=None, count=False):
		context = self._context
		ctx = {'disable_search': True}
		# if self._context.get('disable_search'): 
		
		if ctx.get('disable_search'):
			if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_hod') or self.user_has_groups('odes_crm.group_odes_customer'):
				return super(SaleOrder, self).search(args, offset=offset, limit=limit, order=order, count=count)
			
			report_to_user_ids = self.env.user.report_to_user_ids
			r_ids = [ n.id for n in report_to_user_ids]
			user_domain = [self.env.user.id]
			if r_ids:
				
				for r in r_ids:
					user_domain.append(r)
			# args += [('user_id','in',user_domain)]
			_main_co_id = int(self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.main_company_id', '1') or 1)
			if self.env.company.id == _main_co_id:  # v16: replaced hardcoded [1] with ir.config_parameter
				args += ['|','|',('company_id','=',_main_co_id),('company_id','=',False),('user_id','in',user_domain)]
			else:
				args += [('user_id','in',user_domain)]
		res = super(SaleOrder, self).search(args, offset=offset, limit=limit, order=order, count=count)
		return res

	@api.model
	def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
		ctx = {'disable_search': True}
		# if self._context.get('disable_search'):  
		if ctx.get('disable_search'):
			if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_hod') or self.user_has_groups('odes_crm.group_odes_customer'):
				return super(SaleOrder, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
  
			report_to_user_ids = self.env.user.report_to_user_ids
			r_ids = [ n.id for n in report_to_user_ids]
			user_domain = [self.env.user.id]
			if r_ids:                
				for r in r_ids:
					user_domain.append(r)
			# domain += [('user_id','in',user_domain)]
			_main_co_id = int(self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.main_company_id', '1') or 1)
			if self.env.company.id == _main_co_id:  # v16: replaced hardcoded [1] with ir.config_parameter
				domain += ['|','|',('company_id','=',_main_co_id),('company_id','=',False),('user_id','in',user_domain)]
			else:
				domain += [('user_id','in',user_domain)]

		res = super(SaleOrder, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
		return res

	def print_icon_quotation(self):
		if self.opportunity_id:				
			if self.opportunity_id.stage_id.name == 'Quotation' and self.opportunity_id.is_iconnexion:
				proposal_stage_id = self.env['crm.stage'].search([('name','=','DIP')])
				if proposal_stage_id:
					self.opportunity_id.with_context({'icon_view': 1,}).write({'stage_id': proposal_stage_id.id})
		return self.env.ref('iconnexion_custom.report_quotation_mccoy').report_action(self)

	def button_open_pi(self):
		
		if self.date_order:
			product_ids = self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.default_bank_charges_product_id')
			product_id =  self.env['product.product'].browse(int(product_ids)).exists()
			if not product_id:
				vals = self._prepare_bank_charges_product()
				product_id = self.env['product.product'].create(vals)
				self.env['ir.config_parameter'].sudo().set_param('iconnexion_custom.default_bank_charges_product_id', product_id.id)

			line_vals = {
				'name': 'Bank Charges',
				'price_unit': self.bank_charges,
				'quote_price_unit': self.bank_charges,
				'product_uom_qty': 1.0,
				'spq': 1.0,
				'sale_delay': 1.0,
				'product_id': product_id.id,
				'product_uom': product_id.uom_id.id,
				
			}
			if self.is_iconnexion and self.is_generate_proforma_to_process:
				if self.amount_total <= self.min_order:			
					self.write({'order_line' : [(0, 0,line_vals)]
							 })
			
			if self.is_iconnexion and self.is_generate_proforma:
				if self.amount_total <= self.min_order:			
					self.write({'order_line' : [(0, 0,line_vals)]
							 })

			if self.is_iconnexion and self.is_generate_proforma_partial_before_delivery:
				if self.amount_total <= self.min_order:			
					self.write({'order_line' : [(0, 0,line_vals)]
							 })

			if self.is_iconnexion and self.is_generate_proforma_partial:
				if self.amount_total <= self.min_order:			
					self.write({'order_line' : [(0, 0,line_vals)]
							 })
					
			seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.date_order))
			sequence = self.env['ir.sequence'].next_by_code('proforma.invoice', sequence_date=seq_date) or _('New')
			self.write({'is_proforma_invoice':True,'proforma_number': sequence})
		if self.is_generate_proforma:
			# notify CS
			self.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
								'iconnexion_custom.cs_notif_generate_pi',
							values={'part_number': self,},
							subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
							partner_ids=[],
							subject='Notify Generate PI '+ self.name,                            
					) 


	def button_open_pi_partial(self):
		seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.date_order))
		sequence = self.env['ir.sequence'].next_by_code('proforma.invoice', sequence_date=seq_date) or _('New')
		self.write({'is_proforma_invoice':True,'proforma_number': sequence, 'is_pi_clear':False,})
		if self.is_generate_proforma:
			# notify CS
			self.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
								'iconnexion_custom.cs_notif_generate_pi',
							values={'part_number': self,},
							subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
							partner_ids=[],
							subject='Notify Generate PI '+ self.name,                            
					) 


	def print_icon_so(self):
		return self.env.ref('iconnexion_custom.report_quotation_icon').report_action(self)
		
	def get_usd_value(self, value):
		self.ensure_one()
		currency = self.currency_id
		us_currency_ids = self.env['res.currency'].search([('name','=','USD')],limit=1)

		us_currency = self.env['res.currency'].browse(us_currency_ids[0].id)

		if currency == us_currency:
			return value
		else:
			return currency._convert(value, us_currency, self.company_id, self.date_order or fields.Date.today())

	def get_usd_total_value(self, unit_price, quantity):
		limited_unit_price = round(self.get_usd_value(unit_price), 2)
		return limited_unit_price*quantity


	def button_approve(self):
		context = dict(self.env.context or {})
		for sale in self:
			sale.is_lower_margin = True
		return True


	def button_combine(self):
		if self.order_line:
			product_ids = []
			counter = 1
			quantity = 0
			for line in self.order_line:
				if line.product_template_id.id not in product_ids:
					product_ids.append(line.product_template_id.id)
			for data in product_ids:
				search_order_line = self.env['sale.order.line'].search([('order_id','=',self.id),('product_template_id','=', data),('is_combine','=', True)])
				keep_id = []
				delete_ids = []
				if len(search_order_line) > 1: 
					for line in search_order_line:
						# print(line.id)
						if counter == 1:
							keep_id.append(line.id)
						else:
							delete_ids.append(line.id)
						counter+=1

						quantity += line.product_uom_qty
						# print("quantity:::",quantity)
				keep_line = self.env['sale.order.line'].search([('order_id','=',self.id),('id','=', keep_id)])
				keep_line.product_uom_qty = quantity
				delete_line = self.env['sale.order.line'].search([('order_id','=',self.id),('id','in', delete_ids)])
				delete_line.unlink()

	# v16: duplicate definitions removed — only the last one was active in Python anyway
	def button_quote_crm(self):
		context = dict(self.env.context or {})
		# looping dan create
		list_order_line = []
		date_now = fields.Datetime.now()
		for sale in self:
			# print(sale,'222222222')
			if len(sale.order_line) > 1:
				raise ValidationError("You have product in Quotation Before, please remove it")

			
			if sale.opportunity_id:				
				# print(sale.opportunity_id)
				if (sale.opportunity_id.stage_id.name == 'Proposal' or sale.opportunity_id.stage_id.name == 'New') and sale.opportunity_id.is_iconnexion:
					proposal_stage_id = self.env['crm.stage'].search([('name','=','Quotation')])
					# print(proposal_stage_id)
					if proposal_stage_id:
						sale.opportunity_id.with_context({'icon_view': 1,}).write({'stage_id': proposal_stage_id.id})
						#print(sale.opportunity_id.with_context({'icon_view': 1,}).write({'stage_id'}: proposal_stage_id.id))

				for part in sale.opportunity_id.odes_part_ids:
					if part.product_id:
						moqs = part.product_id.product_tmpl_id.moq_ids.filtered(lambda line: (line.product_variant_id==part.product_id or not line.product_variant_id) )
						moq_id = False
						r_code = 0
						moq = 0
						spq = part.product_id.product_tmpl_id.qty_multiply
						if moqs:
							moq = moqs[0].min_qty
							r_code = moqs[0].r_code
							moq_id = moqs[0].id
						sale_delay = (int(part.product_id.custom_lead_time_by_weeks) * 7 )
						# print ('testaetaetaet',part.product_id.custom_lead_time_by_weeks,'sdfadfadf',sale_delay)
						list_order_line.append((0, 0, {'name':part.product_id.name,
													'product_id':part.product_id.id,
													'quote_price_unit':part.quoted_price,
													'price_unit':part.quoted_price,
													'icon_sale_price' : part.product_id.product_tmpl_id.list_price,
													'product_uom_qty': sale.opportunity_id.annual_qty,
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
			# relativedelta(days=-1 or 0.0,weekday=WE(-1))
			# sale.write({'order_line':[(0,0,{'product_id':28584,'name':'testaetaetesatetaest','customer_lead':0,'price_unit': 0,'product_uom_qty':0})] })
			sale.write({'order_line':list_order_line })
		return True

	def query_fix_data_price_unit(self):
		# v16: raw SQL UPDATE replaced with ORM write() so computed fields
		# (price_subtotal, margin, etc.) are properly recomputed and audit log is kept.
		# sudo() is used because this is a maintenance/fix utility called by admin.
		sale_line_obj = self.env['sale.order.line']
		lines = sale_line_obj.search([])
		# lines = sale_line_obj.search([('order_id','=',5819)])
		for line in lines:
			line.sudo().write({'price_unit': line.quote_price_unit})

	# def action_quotation_send(self):
	# 	if self.is_iconnexion and not self.env.user.has_group('iconnexion_custom.group_iconnexion_sales_manager'):
	# 		raise ValidationError("Send Email Rights is Reserved to Admin")

	# 	# if self.is_iconnexion and not self.attachment_count:
	# 	#     raise ValidationError("Please attach a document of Customer PO before sending Quotation !")

	# 	return super(SaleOrder, self).action_quotation_send()

	def action_quotation_send(self):
		''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
		self.ensure_one()
		
		template_id = self._find_mail_template()
		if self.is_iconnexion:
			template_id = self._find_ack_mail_template(force_confirmation_template=True)			 
			if self.opportunity_id.stage_id.name == 'Quotation' and self.opportunity_id.is_iconnexion:
				proposal_stage_id = self.env['crm.stage'].search([('name','=','DIP')])
				if proposal_stage_id:
					self.opportunity_id.with_context({'icon_view': 1,}).write({'stage_id': proposal_stage_id.id})
		
		if self.is_iconnexion and not self.env.user.has_group('iconnexion_custom.group_iconnexion_sales_manager'):
			raise ValidationError("Send Email Rights is Reserved to Admin")

		lang = self.env.context.get('lang')
		template = self.env['mail.template'].browse(template_id)
		if template.lang:
			lang = template._render_lang(self.ids)[self.id]
		ctx = {
			'default_model': 'sale.order',
			'default_res_id': self.ids[0],
			'default_use_template': bool(template_id),
			'default_template_id': template_id,
			'default_composition_mode': 'comment',
			'mark_so_as_sent': True,
			'custom_layout': "mail.mail_notification_paynow",
			'proforma': self.env.context.get('proforma', False),
			'force_email': True,
			'model_description': self.with_context(lang=lang).type_name,
		}
		return {
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'views': [(False, 'form')],
			'view_id': False,
			'target': 'new',
			'context': ctx,
		}

	def button_create_pi(self):
		context = dict(self.env.context or {})
		if self.is_iconnexion and self.is_generate_proforma_to_process or self.is_generate_proforma_partial_before_delivery or self.is_generate_proforma_partial or self.is_generate_proforma:
			context['active_ids'] = [self.id]
			context['for_pi'] = True
			self.with_context(context).action_create_proforma_invoice()
		return True

	def action_confirm(self, is_pi_clear=[], is_generate_proforma_to_process=[], is_generate_proforma_partial=[],is_generate_proforma_partial_before_delivery=[]):
		context = dict(self.env.context or {})
		#unable confirm because of PI isn't created yet
		if self.is_proforma_invoice and not self.is_pi_clear:
			raise ValidationError("Please Check PI Payment Before Confirm")

		if self.is_iconnexion and not self.env.user.has_group('iconnexion_custom.group_iconnexion_icon_confirm_quo'):
			raise ValidationError("Confirm Order Rights is Reserved to Admin")
		for line in self.order_line:
			if self.is_iconnexion:
				if line.is_lower_margin :
					raise ValidationError("Please Check New Pricing Request")
				if line.product_uom_qty == 0 or line.spq == 0 or line.quote_price_unit == 0 or line.sale_delay == 0:
					raise ValidationError("Please Check SPQ, U/Price, Total price, L/T Value")

		if self.is_iconnexion and self.state == 'draft' :
			self._send_acknowledgen_mail()

		if self.is_iconnexion and not self.attachment_count:
			raise ValidationError("Please attach a document of Customer PO before confirming !")    

		if self.is_iconnexion and not self.client_order_ref:
			raise ValidationError("Please Check Customer PO!")       
		
		if self.is_iconnexion:
			if not self.opportunity_id and not self.contact_id:
				raise ValidationError("Please check Contact and Opportunity field before confirming !")
			context['sale_order_id'] = self.id
			# if self.is_generate_proforma_to_process and self.is_pi_clear == False:	
			# 	raise ValidationError("Please Check PI Before Confirm")
			# if self.is_generate_proforma_partial and self.is_pi_clear == False:		
			# 	raise ValidationError("Please Check PI Before Confirm")	
			# if self.is_generate_proforma_partial_before_delivery and self.is_pi_clear == False:	
			# 	raise ValidationError("Please Check PI Before Confirm")
			
			
			

		if self.opportunity_id:

			if self.opportunity_id.stage_id.name != 'Design Win' and self.opportunity_id.is_iconnexion:
				if self.opportunity_id.stage_id.name != 'Won':
					raise ValidationError("Please Check CRM Stage before Create SO")
						
			if self.opportunity_id.stage_id.name == 'Design Win' and self.opportunity_id.is_iconnexion:
				proposal_stage_id = self.env['crm.stage'].search([('name','=','Won'),('id','=',4)],limit=1)
				if proposal_stage_id:
					self.opportunity_id.with_context({'icon_view': 1,}).write({'stage_id': proposal_stage_id.id})

		is_pi_clear.append(self.is_pi_clear)
		is_generate_proforma_to_process.append(self.is_generate_proforma_to_process)
		is_generate_proforma_partial.append(self.is_generate_proforma_partial)
		is_generate_proforma_partial_before_delivery.append(self.is_generate_proforma_partial_before_delivery)
		res =  super(SaleOrder, self.with_context(context)).action_confirm()
		if self.is_iconnexion:
			context['sale_order_id'] = self.id
			if is_generate_proforma_to_process[0] and is_pi_clear[0] == False:
				raise ValidationError("Please Check PI Before Confirm")
			if is_generate_proforma_partial[0] and is_pi_clear[0] == False:		
				raise ValidationError("Please Check PI Before Confirm")	
			if is_generate_proforma_partial_before_delivery[0] and is_pi_clear[0] == False:		
				raise ValidationError("Please Check PI Before Confirm")

		if self.is_iconnexion and context.get('use_default') and self.is_generate_proforma:#and tt payment terms
			# 2) TT in advance before delivery (get customer PO, then SO, issue PI to customer 1wk before supplier delivery date, after finance confirm receive payment just can release the goods)
			context['active_ids'] = [self.id]
			context['for_pi'] = True
			# self.with_context(context).action_create_proforma_invoice()
			# sent notify to cs david 27 09 2022
		search_name = self.name.replace('QUO', 'SO')
		search_id = self.env['sale.order'].search([('name', '=', search_name)], limit=1)
		this_id = search_id.id
		if self.is_iconnexion:
			return {
				'name': _('Sale Orders'),
				'view_mode': 'form',
				'res_model': 'sale.order',
				'views': [(self.env.ref('sale.view_order_form').id, 'form')],
				'type': 'ir.actions.act_window',
				'res_id': this_id,
			}
		else:
			return res




	def _find_ack_mail_template(self, force_confirmation_template=False):#davidsetiadi11
		template_id = False

		if force_confirmation_template or (self.state == 'sale' and not self.env.context.get('proforma', False)):
			template_id = int(self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.mail_template_ack_confirmation'))
			template_id = self.env['mail.template'].search([('id', '=', template_id)]).id
			if not template_id:
				template_id = self.env['ir.model.data'].xmlid_to_res_id('iconnexion_custom.mail_template_ack_confirmation', raise_if_not_found=False)
		# if not template_id:
		#     template_id = self.env['ir.model.data'].xmlid_to_res_id('sale.email_template_edi_sale', raise_if_not_found=False)

		return template_id


	def _send_acknowledgen_mail(self):
		if self.env.su:
			# sending mail in sudo was meant for it being sent from superuser
			self = self.with_user(SUPERUSER_ID)
		template_id = self._find_ack_mail_template(force_confirmation_template=True)
		if template_id:
			# print (error)
			#sent to salesman and customer service
			partner_ids = []
			for cs in self.company_id.icon_customer_service_ids:
				partner_ids.append(cs.id)
			if self.user_id:
				print ('append to partner , will sent to salesman, disable due mike email')
			for order in self:
				order = order.with_user(2)
				order.with_context(force_send=True,icon_skip_partner=True).message_post_with_template(template_id, composition_mode='comment',partner_ids=partner_ids, email_layout_xmlid="mail.mail_notification_paynow")


	def _compute_count_attachment(self):
		for so in self:
			# so.attachment_count = self.env['ir.attachment'].sudo().search_count(
			#     [('res_id', '=', self.id), ('res_model', '=', 'sale.order')])
			so.attachment_count = len(self.attachment_ids)

	def action_create_proforma_invoice(self):
		self._create_proforma()

	

	def _create_invoices(self, grouped=False, final=False, date=None):
		moves = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final)               
		#search product bank charges

		product_ids = self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.default_bank_charges_product_id')
		product_id =  self.env['product.product'].browse(int(product_ids)).exists()

		if not product_id:
			vals = self._prepare_bank_charges_product()
			product_id = self.env['product.product'].create(vals)
			self.env['ir.config_parameter'].sudo().set_param('iconnexion_custom.default_bank_charges_product_id', product_id.id)

		line_vals = {
			'name': 'Bank Charges',
			'price_unit': self.bank_charges,
			'quantity': 1.0,
			'product_id': product_id,
			'product_uom_id': product_id.uom_id
			
		}
		if self.is_iconnexion and self.is_generate_proforma and self.is_pi_clear == False:	
			raise ValidationError(_('this PI has not been paid'))
		if self.is_iconnexion and self.is_generate_proforma_partial and self.is_pi_clear == False:	
			raise ValidationError(_('this PI has not been paid'))
		if self.is_iconnexion and self.is_generate_proforma_partial_before_delivery == True and self.is_pi_clear == False:
			raise ValidationError(_("%s cannot create an invoice ") % (self.payment_term_id.name))
		# if self.is_iconnexion and self.is_generate_proforma_partial_before_delivery and self.is_pi_clear == False:	
		# 	raise ValidationError(_('this PI has not been paid'))
		if self.is_iconnexion and self.amount_total <= 300 and (self.is_generate_proforma or self.is_generate_proforma_to_process or self.is_generate_proforma_partial or self.is_generate_proforma_partial_before_delivery):
			name = self.name.replace('SO', 'INV') #proforma Invoice			
			moves.write({'invoice_line_ids' : [(0, 0,line_vals)],
						  'name':name})
		# elif self.is_iconnexion and self.is_generate_proforma_to_process:
		# 	name = self.name.replace('SO', 'INV') #proforma Invoice			
		# 	moves.write({'name':name})
		# 	moves.write({'invoice_line_ids' : [(0, 0,line_vals)],
		# 				  'name':name})
		elif self.is_iconnexion:
			name = self.name.replace(self.company_id.quotation_new_prefix, 'INV') #Invoice
			moves.write({'name' : name })
				
		return moves

	def _prepare_bank_charges_product(self):
		return {
			'name': 'Bank Charges',
			'type': 'service',
			'invoice_policy': 'order',                     
			'company_id': False,
		}


	def action_icon_quotation_reason(self):

		return {
			'type': 'ir.actions.act_window',
			'name': 'Request Lower Margin',
			'res_model': 'icon.quotation.reason.wizard',
			'view_mode': 'form',
			'target': 'new',
			'context': {'active_id': self._context.get('active_id'), 'active_model': self._context.get('active_model')},
		}

	def action_icon_quotation_approve(self):

		return {
			'type': 'ir.actions.act_window',
			'name': 'View Request',
			'res_model': 'icon.quotation.approve.wizard',
			'view_mode': 'form',
			'target': 'new',
			'context': {'active_id': self._context.get('active_id'), 'active_model': self._context.get('active_model')},
		}


	def create_proforma_invoice(self):
		name = self.name.replace('SO', 'INV') #proforma Invoice		
		seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.date_order))
		sequence = self.env['ir.sequence'].next_by_code('proforma.invoice', sequence_date=seq_date) or _('New')
		product_ids = self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.default_bank_charges_product_id')
		product_id =  self.env['product.product'].browse(int(product_ids)).exists()
		self.write({'is_pi_clear':False,'is_proforma_invoice':True,})


		if not product_id:
			vals = self._prepare_bank_charges_product()
			product_id = self.env['product.product'].create(vals)
			self.env['ir.config_parameter'].sudo().set_param('iconnexion_custom.default_bank_charges_product_id', product_id.id)

		line_vals = {
			'name': 'Bank Charges',
			'account_id': self.company_id.pi_credit_id.id,
			'price_unit': self.bank_charges,
			'quantity': 1.0,
			'product_id': product_id,
			'product_uom_id': product_id.uom_id
			
		}
		account_move = self.env['account.move'].create({
            'name': sequence,
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'contact_id': self.contact_id.id, 
            'is_proforma_invoice': True,
            'state': 'draft',
            'invoice_payment_term_id': self.payment_term_id.id,
            'amount_total': self.amount_total,
            'sale_order_id': self.id,

        })
		
		for line in self.order_line:
			move = self.env['account.move.line'].create({
                'move_id': account_move.id,
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'product_uom_id': line.product_uom.id,
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
                'price_subtotal': line.price_subtotal,
                'account_id': self.company_id.pi_credit_id.id,
				'tax_ids': [(6, 0, line.tax_id.ids)],

            })
		if self.amount_total <= 300:
			account_move.write({'invoice_line_ids' : [(0, 0,line_vals)]})


	def _prepare_proforma(self):
		"""
		Prepare the dict of values to create the new invoice for a sales order. This method may be
		overridden to implement custom invoice generation (making sure to call super() to establish
		a clean extension chain).
		"""
		self.ensure_one()
		seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.date_order))
		sequence = self.env['ir.sequence'].next_by_code('proforma.invoice', sequence_date=seq_date) or _('New')
		journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
		self.write({'is_pi_clear':False,'is_proforma_invoice':True,})
		if not journal:
			raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))
		
		invoice_vals = {
			'name': sequence,
			'ref': self.client_order_ref or '',
			'move_type': 'out_invoice',
			'narration': self.note,
			'currency_id': self.pricelist_id.currency_id.id,
			'campaign_id': self.campaign_id.id,
			'medium_id': self.medium_id.id,
			'source_id': self.source_id.id,
			'user_id': self.user_id.id,
			'invoice_user_id': self.user_id.id,
			'team_id': self.team_id.id,
			'partner_id': self.partner_invoice_id.id,
			'partner_shipping_id': self.partner_shipping_id.id,
			'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(self.partner_invoice_id.id)).id,
			'partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
			'journal_id': journal.id,  # company comes from the journal
			'invoice_origin': self.name,
			'invoice_payment_term_id': self.payment_term_id.id,
			'payment_reference': self.reference,
			'transaction_ids': [(6, 0, self.transaction_ids.ids)],
			'invoice_line_ids': [],
			'company_id': self.company_id.id,
			'is_proforma_invoice':True,
			'sale_order_id': self.id,
		}
		return invoice_vals

	@api.model
	def _nothing_to_proforma_error(self):
		msg = _("""Cannot create an Pro-Forma Invoice!\n
Order Line is empty.
		""")
		return UserError(msg)	
	

	def _get_invoiceable_lines(self, final=False):
		"""Return the invoiceable lines for order `self`."""
		down_payment_line_ids = []
		invoiceable_line_ids = []
		pending_section = None
		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

		for line in self.order_line:
			if line.display_type == 'line_section':
				# Only invoice the section if one of its lines is invoiceable
				pending_section = line
				continue
			if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
				continue
			if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
				if line.is_downpayment:
					# Keep down payment lines separately, to put them together
					# at the end of the invoice, in a specific dedicated section.
					down_payment_line_ids.append(line.id)
					continue
				if pending_section:
					invoiceable_line_ids.append(pending_section.id)
					pending_section = None
				invoiceable_line_ids.append(line.id)

		return self.env['sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)


	def _create_proforma(self, grouped=False, final=False, date=None):
		if not self.env['account.move'].check_access_rights('create', False):
			try:
				self.check_access_rights('write')
				self.check_access_rule('write')
			except AccessError:
				return self.env['account.move']

		# 1) Create invoices.
		invoice_vals_list = []
		invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
		product_ids = self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.default_bank_charges_product_id')
		product_id =  self.env['product.product'].browse(int(product_ids)).exists()

		if not product_id:
			vals = self._prepare_bank_charges_product()
			product_id = self.env['product.product'].create(vals)
			self.env['ir.config_parameter'].sudo().set_param('iconnexion_custom.default_bank_charges_product_id', product_id.id)

		line_vals = {
			'name': 'Bank Charges',
			'account_id': self.company_id.pi_credit_account_id.id,
			'price_unit': self.bank_charges,
			'quantity': 1.0,
			'product_id': product_id,
			'product_uom_id': product_id.uom_id
			
		}
		for order in self:
			order = order.with_company(order.company_id)
			current_section_vals = None
			down_payments = order.env['sale.order.line']

			invoice_vals = order._prepare_proforma()
			invoiceable_lines = order._get_invoiceable_lines(final)

			if not any(not line.display_type for line in invoiceable_lines):
				continue

			invoice_line_vals = []
			down_payment_section_added = False
			for line in invoiceable_lines:
				if not down_payment_section_added and line.is_downpayment:
					# Create a dedicated section for the down payments
					# (put at the end of the invoiceable_lines)
					invoice_line_vals.append(
						(0, 0, order._prepare_down_payment_section_line(
							sequence=invoice_item_sequence,
						)),
					)
					down_payment_section_added = True
					invoice_item_sequence += 1
				invoice_line_vals.append(
					(0, 0, line._prepare_proforma_line(
						sequence=invoice_item_sequence,
					)),
				)
				invoice_item_sequence += 1

			if order.amount_total <= 300:
				invoice_line_vals.append(
					(0, 0, line_vals),
				)
			invoice_vals['invoice_line_ids'] += invoice_line_vals
			invoice_vals_list.append(invoice_vals)

			print(invoice_line_vals,'invoice_vals_list')

		

		if not invoice_vals_list:
			raise self._nothing_to_proforma_error()

		# 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
		if not grouped:
			new_invoice_vals_list = []
			invoice_grouping_keys = self._get_invoice_grouping_keys()
			invoice_vals_list = sorted(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys])
			for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
				origins = set()
				payment_refs = set()
				refs = set()
				ref_invoice_vals = None
				for invoice_vals in invoices:
					if not ref_invoice_vals:
						ref_invoice_vals = invoice_vals
					else:
						ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
					origins.add(invoice_vals['invoice_origin'])
					payment_refs.add(invoice_vals['payment_reference'])
					refs.add(invoice_vals['ref'])
				ref_invoice_vals.update({
					'ref': ', '.join(refs)[:2000],
					'invoice_origin': ', '.join(origins),
					'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
				})
				new_invoice_vals_list.append(ref_invoice_vals)
			invoice_vals_list = new_invoice_vals_list
		if len(invoice_vals_list) < len(self):
			SaleOrderLine = self.env['sale.order.line']
			for invoice in invoice_vals_list:
				sequence = 1
				for line in invoice['invoice_line_ids']:
					line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
					sequence += 1

		# Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
		# sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
		moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

		# 4) Some moves might actually be refunds: convert them if the total amount is negative
		# We do this after the moves have been created since we need taxes, etc. to know if the total
		# is actually negative or not
		if final:
			moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
		for move in moves:
			move.message_post_with_view('mail.message_origin_link',
				values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
				subtype_id=self.env.ref('mail.mt_note').id
			)
		return moves
	

class SaleOrderLine(models.Model):
	_name = "sale.order.line"
	_inherit = ['sale.order.line', 'mail.thread', 'mail.activity.mixin'] 


	@api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
	def _compute_invoice_status(self):
		"""
		Compute the invoice status of a SO line. Possible statuses:
		- no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
		  invoice. This is also hte default value if the conditions of no other status is met.
		- to invoice: we refer to the quantity to invoice of the line. Refer to method
		  `_get_to_invoice_qty()` for more information on how this quantity is calculated.
		- upselling: this is possible only for a product invoiced on ordered quantities for which
		  we delivered more than expected. The could arise if, for example, a project took more
		  time than expected but we decided not to invoice the extra cost to the client. This
		  occurs onyl in state 'sale', so that when a SO is set to done, the upselling opportunity
		  is removed from the list.
		- invoiced: the quantity invoiced is larger or equal to the quantity ordered.
		"""
		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
		for line in self:
			if line.state not in ('sale', 'done'):
				line.invoice_status = 'no'
			elif line.state == 'done':
				line.invoice_status = 'no'
			elif line.is_downpayment and line.untaxed_amount_to_invoice == 0:
				line.invoice_status = 'invoiced'
			elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
				line.invoice_status = 'to invoice'
			elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and\
					float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
				line.invoice_status = 'upselling'
			elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
				line.invoice_status = 'invoiced'
			else:
				line.invoice_status = 'no'

	def _prepare_proforma_line(self, **optional_values):
		"""
		Prepare the dict of values to create the new invoice line for a sales order line.

		:param qty: float quantity to invoice
		:param optional_values: any parameter that should be added to the returned invoice line
		"""
		self.ensure_one()
		res = {
			'display_type': self.display_type,
			'sequence': self.sequence,
			'name': self.name,
			'product_id': self.product_id.id,
			'product_uom_id': self.product_uom.id,
			'quantity': self.qty_to_invoice,
			'discount': self.discount,
			'account_id': self.order_id.company_id.pi_credit_account_id.id,
			'price_unit': self.price_unit,
			'tax_ids': [(6, 0, self.tax_id.ids)],
			'analytic_account_id': self.order_id.analytic_account_id.id,
			'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
			'sale_line_ids': [(4, self.id)],
		}
		if optional_values:
			res.update(optional_values)
		if self.display_type:
			res['account_id'] = False
		return res

	api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state', 'order_id.payment_term_id')
	def _get_to_invoice_qty(self):
		"""
		Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
		calculated from the ordered quantity. Otherwise, the quantity delivered is used.
		"""
		for line in self:
			if line.order_id.state in ['sale', 'done']:
				if line.product_id.invoice_policy == 'order':
					line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
				else:
					line.qty_to_invoice = line.qty_delivered - line.qty_invoiced

			elif line.is_iconnexion and line.order_id.is_generate_proforma_to_process:
				line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced

			elif line.is_iconnexion and line.order_id.is_generate_proforma_partial:
				line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced

			elif line.is_iconnexion and line.order_id.is_generate_proforma_partial_before_delivery:
				line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced

			elif line.is_iconnexion and line.order_id.is_generate_proforma:
				line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced

			else:
				line.qty_to_invoice = 0
				
	@api.depends('product_uom_qty', 'product_id','quote_price_unit')
	def _compute_margin(self):
		for line in self:
			line.s_margin = 0
			line.s_margin_char = "%"
			line.a_margin = 0
			line.a_margin_char = "%"
			line.total_a_margin = 0
			# line.total_a_margin_char = "%"
			sale_price = line.icon_sale_price
			cost_price = line.cost_price
			if line.quote_price_unit > 0 :
				line.s_margin = s_margin = (line.quote_price_unit - sale_price )/ line.quote_price_unit
				line.s_margin_char = str(round(s_margin*100,2)) + ' %'
			# if line.cost_price > 0:
				line.a_margin = a_margin = (line.quote_price_unit - cost_price )/ line.quote_price_unit
				line.a_margin_char = str(round(a_margin*100,2)) + ' %'
			line.total_a_margin = (line.quote_price_unit - cost_price) * line.product_uom_qty

	def _compute_rcode(self):
		for line in self:
			line.brand = ''
			line.r_code = ''
			line.customer_request_date2 = line.customer_request_date
			if line.product_id.product_tmpl_id.product_brand_id:
				line.brand = line.product_id.product_tmpl_id.product_brand_id.name
			if line.moq_id:
				line.r_code = line.moq_id.r_code


	# @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
	@api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'invoice_lines.move_id.payment_state')
	def _compute_payment_state(self):
		"""
		Compute the payment status of a SO line. Possible statuses:
		- no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
		  invoice. This is also hte default value if the conditions of no other status is met.
		- to invoice: we refer to the quantity to invoice of the line. Refer to method
		  `_get_to_invoice_qty()` for more information on how this quantity is calculated.
		- upselling: this is possible only for a product invoiced on ordered quantities for which
		  we delivered more than expected. The could arise if, for example, a project took more
		  time than expected but we decided not to invoice the extra cost to the client. This
		  occurs onyl in state 'sale', so that when a SO is set to done, the upselling opportunity
		  is removed from the list.
		- invoiced: the quantity invoiced is larger or equal to the quantity ordered.
		"""
		
		for line in self:
			payment_state = 'not_paid'
			for invoice_line in line.invoice_lines:
				payment_state = invoice_line.move_id.payment_state
				if payment_state != 'not_paid':
					break
				# if invoice_line.move_id.state != 'cancel':
			if payment_state != 'not_paid':
				if line.order_id.is_iconnexion:
					line.with_context({'payment_paid':True,'sale_order_id':line.order_id.id})._action_launch_stock_rule()

			line.payment_state = payment_state


	sales_history_ids = fields.One2many(related="product_id.icon_sales_history_ids", string="Sales History")
	quote_price_unit = fields.Float('Quoted Unit Price', required=False, digits='Quote Product Price', default=0.0)
	analyze_order_id = fields.Many2one('sale.order', compute="_get_analyze_order_id", store=True)
	# last_price_unit = fields.Float('Last Price', compute="compute_last_price")
	# moq = fields.Float('MOQ')
	# spq = fields.Float('SPQ')
	r_code = fields.Char('R. Code (Computed)', compute="_compute_rcode")
	icon_sale_price = fields.Float('Sale Price')#sale pakai moq apabila ada
	# a_moq  = fields.Float('A. MOQ')
	# a_spq  = fields.Float('A. SPQ')
	ar_code = fields.Char('R. Code')
	customer_request_date2 = fields.Date('Customer Request Date (Computed)', compute="_compute_rcode")
	brand  = fields.Char('Brand', compute="_compute_rcode")
	cost_price = fields.Float(string="Cost Price", compute="_compute_cost_price")
	s_margin = fields.Float('S. Margin', compute="_compute_margin")
	s_margin_char = fields.Char('S. Margin Char', compute="_compute_margin")
	a_margin = fields.Float('A. Margin', compute="_compute_margin")
	a_margin_char = fields.Char('A. Margin Char', compute="_compute_margin")
	total_a_margin = fields.Float('Total A. Margin', compute="_compute_margin")
	# total_a_margin_char = fields.Float('Total A. Margin Char', compute="_compute_margin")
	# v16: mccoy.product.moq not available (mccoy_custom uninstallable); field disabled
	# moq_id = fields.Many2one('mccoy.product.moq',string='MOQ ID')
	# lead_time = customer_lead sale_delay
	reason = fields.Char('Reason')
	is_iconnexion = fields.Boolean(related='order_id.is_iconnexion')
	is_generate_proforma = fields.Boolean(related='order_id.is_generate_proforma')
	is_combine = fields.Boolean('Combine', default=False)
	payment_state = fields.Selection(selection=[
		('not_paid', 'Not Paid'),
		('in_payment', 'In Payment'),
		('paid', 'Paid'),
		('partial', 'Partially Paid'),
		('reversed', 'Reversed'),
		('invoicing_legacy', 'Invoicing App Legacy')],
		string="Payment Status", store=True, readonly=True, copy=False, tracking=True,
		compute='_compute_payment_state')

	moq = fields.Float('MOQ', digits='iCon MOQ')
	spq = fields.Float('SPQ', digits='iCon MOQ')
	a_moq  = fields.Float('A. MOQ', digits='iCon MOQ')
	a_spq  = fields.Float('A. SPQ', digits='iCon MOQ')
	sale_delay = fields.Float('L/T', default=1, digits='iCon MOQ')
	date_input = fields.Datetime('Date Request Lower Margin')
	date_approve = fields.Datetime('Date Aprrove Lower Margin')
	approve_user_id = fields.Many2one('res.users',string='User Approve')
	request_user_id = fields.Many2one('res.users',string='User Request')
	is_lower_margin = fields.Boolean('Lower Margin',default=False)
	is_request_margin = fields.Boolean('Request Lower Margin',default=False)



	icon_purchase_id = fields.Many2one('purchase.order', string="ICPO Number", copy=False)
	icon_purchase_line_id = fields.Many2one('purchase.order.line', string="ICPO Number Line",copy=False)
	# icon_qty_to_po = fields.Float(compute='_compute_qty_to_po', string='ICPO Quantity', store=True, readonly=True,
	#                               digits='Product Unit of Measure')
	customer_request_date = fields.Date('Customer Request Date')#Request Date from Customer on Fri
	icpo_request_deliver_date = fields.Date('ICPO Request Delivery Date') #ICPO request delivery date. 1 week before Customer req date
	delivery_date = fields.Date('Delivery Date') #Delivery Date, each Line have different delivery date
	icon_scheduled_date = fields.Date('Scheduled Date (Icon)')
	# Supplier Delivery Date if supplier change delivery date, SO have log note and system auto email to salesman
	committed_date = fields.Datetime('Committed Date', copy=True,
									  help="This is the delivery date promised to the customer. "
										   "If set, the delivery order will be scheduled based on "
										   "this date rather than product lead times.")

	icon_purchase_ids = fields.Many2many('purchase.order.line', 'sale_order_line_purchase_order_line_rel' ,'purchase_order_line_id','sale_order_line_id', string="PO Number Line", copy=False)
	value_stock_aging = fields.Float(compute='_compute_value_stock_aging',string='Value Stock Aging',store=False)
	icon_committed_history_ids = fields.One2many('icon.committeddate.history','sale_line_committeddate_history_id', string="Committed History Date")
	client_order_ref_rel = fields.Char(related='order_id.client_order_ref',string="Customer PO")

	supplier_name_id = fields.Many2one('res.partner',compute='_compute_po_reference',string='Supplier Name',store=True)
	# salesperson_id = fields.Many2one('res.users',compute='_compute_so_reference',string='Salesperson',store=False)
	# customer_po_number = fields.Char(compute='_compute_so_reference',string='Customer PO Number',store=False)
	# SO Reference, Supplier Name, Customer Name, Salesperson.
	# @api.depends('icon_factory_reschedule_date')
	virtual_available_at_date = fields.Float(compute='_compute_qty_at_date',compute_sudo=True, digits='Product Unit of Measure')
	scheduled_date = fields.Datetime(compute_sudo=True,compute='_compute_qty_at_date')
	forecast_expected_date = fields.Datetime(compute_sudo=True,compute='_compute_qty_at_date')
	free_qty_today = fields.Float(compute='_compute_qty_at_date',compute_sudo=True, digits='Product Unit of Measure')
	qty_available_today = fields.Float(compute_sudo=True,compute='_compute_qty_at_date')
	is_pick = fields.Boolean('Pick')
	serial_numbers = fields.Integer(string='No.', compute='_compute_serial_number')

	is_special_price = fields.Boolean(string='Special Price', compute="_compute_is_special_price", store=True)
	current_stock = fields.Float('Current Stock', readonly=True, compute='_compute_current_stock')

	# @api.depends('product_id')
	def _compute_current_stock(self):
		for i in self:
			quantity = 0
			stock_quant_ids = self.env['stock.quant'].search([('product_id', '=', i.product_id.id),('on_hand', '=', True)])
			for stock_quant in stock_quant_ids:
				quantity += stock_quant.available_quantity
				# print(quantity)
			i.current_stock = quantity
			# print(quantity,'1111111111')


	@api.depends('product_id.seller_ids.customer_id', 'order_id.partner_id')
	def _compute_is_special_price(self):
		for product in self:
			if product.product_id.seller_ids:
				for sup in product.product_id.seller_ids:
					if sup.customer_id.id == product.order_id.partner_id.id:
						product.is_special_price = True
						break
					else:
						product.is_special_price = False


	@api.depends('sequence', 'order_id')
	def _compute_serial_number(self):
		for order_line in self:
			if order_line.serial_numbers == 0:
				serial_no = 1
				for line in order_line.mapped('order_id').order_line:
					line.serial_numbers = serial_no
					serial_no += 1
					# print(self.sequence, self.order_id, self, line.serial_numbers)


	@api.depends(
		'product_id', 'customer_lead', 'product_uom_qty', 'product_uom', 'order_id.commitment_date',
		'move_ids', 'move_ids.forecast_expected_date', 'move_ids.forecast_availability')
	def _compute_qty_at_date(self):
		""" Compute the quantity forecasted of product at delivery date. There are
		two cases:
		 1. The quotation has a commitment_date, we take it as delivery date
		 2. The quotation hasn't commitment_date, we compute the estimated delivery
			date based on lead time"""
		treated = self.browse()
		# If the state is already in sale the picking is created and a simple forecasted quantity isn't enough
		# Then used the forecasted data of the related stock.move
		for line in self.sudo().filtered(lambda l: l.state == 'sale'):
			if not line.display_qty_widget:
				continue
			moves = line.move_ids
			line.forecast_expected_date = max(moves.filtered("forecast_expected_date").mapped("forecast_expected_date"), default=False)
			line.qty_available_today = 0
			line.free_qty_today = 0
			for move in moves:
				line.qty_available_today += move.product_uom._compute_quantity(move.quantity, line.product_uom)
				line.free_qty_today += move.product_id.uom_id._compute_quantity(move.forecast_availability, line.product_uom)
			line.scheduled_date = line.order_id.commitment_date or line._expected_date()
			line.virtual_available_at_date = False
			treated |= line

		qty_processed_per_product = defaultdict(lambda: 0)
		grouped_lines = defaultdict(lambda: self.env['sale.order.line'])
		# We first loop over the SO lines to group them by warehouse and schedule
		# date in order to batch the read of the quantities computed field.
		for line in self.sudo().filtered(lambda l: l.state in ('draft', 'sent')):
			if not (line.product_id and line.display_qty_widget):
				continue
			grouped_lines[(line.warehouse_id.id, line.order_id.commitment_date or line._expected_date())] |= line

		for (warehouse, scheduled_date), lines in grouped_lines.items():
			product_qties = lines.mapped('product_id').with_context(to_date=scheduled_date, warehouse=warehouse).read([
				'qty_available',
				'free_qty',
				'virtual_available',
			])
			qties_per_product = {
				product['id']: (product['qty_available'], product['free_qty'], product['virtual_available'])
				for product in product_qties
			}
			for line in lines:
				line.scheduled_date = scheduled_date
				qty_available_today, free_qty_today, virtual_available_at_date = qties_per_product[line.product_id.id]
				line.qty_available_today = qty_available_today - qty_processed_per_product[line.product_id.id]
				line.free_qty_today = free_qty_today - qty_processed_per_product[line.product_id.id]
				line.virtual_available_at_date = virtual_available_at_date - qty_processed_per_product[line.product_id.id]
				line.forecast_expected_date = False
				if line.product_uom and line.product_id.uom_id and line.product_uom != line.product_id.uom_id:
					line.qty_available_today = line.product_id.uom_id._compute_quantity(line.qty_available_today, line.product_uom)
					line.free_qty_today = line.product_id.uom_id._compute_quantity(line.free_qty_today, line.product_uom)
					line.virtual_available_at_date = line.product_id.uom_id._compute_quantity(line.virtual_available_at_date, line.product_uom)
				qty_processed_per_product[line.product_id.id] += line.product_uom_qty
			treated |= lines
		remaining = (self - treated)
		remaining.virtual_available_at_date = False
		remaining.scheduled_date = False
		remaining.forecast_expected_date = False
		remaining.free_qty_today = False
		remaining.qty_available_today = False

	def _get_invoice_qty(self):
		"""
		Compute the quantity invoiced. If case of a refund, the quantity invoiced is decreased. Note
		that this is the case only if the refund is generated from the SO and that is intentional: if
		a refund made would automatically decrease the invoiced quantity, then there is a risk of reinvoicing
		it automatically, which may not be wanted at all. That's why the refund has to be created from the SO
		***Modified so that this function accomodate move line from split by line
		"""
		for line in self:
			qty_invoiced = 0.0
			for invoice_line in line.invoice_lines:
				if invoice_line.move_id.state != 'cancel':
					if invoice_line.move_id.is_proforma_invoice:
						continue
						
					if invoice_line.move_id.move_type == 'out_invoice' and line.is_generate_proforma == False: #Proforma Invoice shouldn't affect Invoiced Qty #14-06-2022
						if invoice_line.is_split_by_line_downpayment:
							continue
						qty_invoiced += invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
					elif invoice_line.move_id.move_type == 'out_refund':
						if not line.is_downpayment or line.untaxed_amount_to_invoice == 0 :
							qty_invoiced -= invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
			#add count +1 if invoice is downpaymetn without invoice lines, to allow downpayment to be counted
			if line.is_downpayment and not len(line.invoice_lines):
				qty_invoiced += 1
			line.qty_invoiced = qty_invoiced
				


	@api.depends('icon_purchase_ids', 'icon_purchase_ids.order_id')
	def _compute_po_reference(self):		
		for line in self:
			line.supplier_name_id = False
			# line.customer_po_number = ''
			if line.icon_purchase_ids:
				for po_line in line.icon_purchase_ids:
					line.supplier_name_id = po_line.order_id.partner_id.id
				
					break #modif david 31 05 2022

	def action_committed_history_wizard(self):
		return {
			'type': 'ir.actions.act_window',
			'name': 'Change Committed Date',
			'res_model': 'icon.committed.date.wizard',
			'view_mode': 'form',
			'target': 'new',
			'context': {'active_id': self._context.get('active_id'), 'active_model': self._context.get('active_model')},
		}

	
	
	def action_view_history_wizard(self):
		return {
			'type': 'ir.actions.act_window',
			'name': 'View Committed Date',
			'res_model': 'icon.committeddate.history',
			'view_mode': 'tree',
			'domain': [('sale_line_committeddate_history_id','=',self.id)],			
			'context': {'active_id': self._context.get('active_id'), 'active_model': self._context.get('active_model')},
		}	

	# Customer Request Date (Sales Order) - Current Date (in Value, By SOL)
	@api.depends('customer_request_date')
	def _compute_value_stock_aging(self):
		for line in self:
			if line.customer_request_date:
				line.value_stock_aging = relativedelta(					
					fields.Date.from_string(line.customer_request_date),fields.Date.from_string(fields.Date.today()) ).days 
			else: 
				line.value_stock_aging = 0

	# v16: _compute_qty_invoiced removed — override used purchase-order fields (qty_received)
	# which don't exist on sale.order.line in v16; let the base sale module handle it.

	@api.model_create_multi
	def create(self, vals_list):
		records = super(SaleOrderLine, self).create(vals_list)
		if self._context.get('import_file'):
			records._onchange_customer_request_date()
		return records
	# def write(self, values):
	#     res = super(SaleOrderLine, self).write(values)
	#     if self._context.get('import_file'):
	#         res._onchange_customer_request_date()  

	#     return res
	@api.depends('product_id')
	def _compute_cost_price(self):
		for line in self:
			line.cost_price = line.product_id.standard_price

	@api.depends('order_id')
	def _get_analyze_order_id(self):
		for line in self:
			line.analyze_order_id = line.order_id

	def save_initial_price(self):
		for line in self:
			if not line.price_unit:
				line.price_unit = line.quote_price_unit

	@api.onchange('customer_request_date')
	def _onchange_customer_request_date(self):        
		if self.customer_request_date:
			self.icpo_request_deliver_date =  self.customer_request_date + relativedelta(days= -7 or 0.0,weekday=WE(-1))
		else:
			self.icpo_request_deliver_date = datetime.now()

	@api.onchange('product_id')
	def product_id_change(self):
		#moq ambil yang paling kecil
		# di order dilimit Orders must be made in multiples of the SPQ
		# custom_lead_time_by_weeks > ganti customerlead
		res = super(SaleOrderLine, self).product_id_change()
		_trading_co_id = int(self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.trading_company_id', '3') or 0)
		if self.company_id.id == _trading_co_id:  # v16: replaced hardcoded 3 with ir.config_parameter
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
					# print ('adfadfadfaaaaaaaaaaaaa',vals['quote_price_unit'])
					
				# vals['quote_price_unit'] = self.product_id.product_tmpl_id.list_price * ( 1 + (self.company_id.min_margin * 0.01) )
				# if self.company_id.min_margin < 100:
				# 	vals['quote_price_unit'] = self.product_id.product_tmpl_id.list_price / ( 1 - ( (self.company_id.min_margin+1) * 0.01) )
				# # (line.quote_price_unit - sale_price )/ line.quote_price_unit
				# if self.product_id.product_tmpl_id.list_price == 0:
				# 	vals['quote_price_unit'] = 0

				# vals['price_unit'] =  vals['quote_price_unit']#self.product_id.product_tmpl_id.list_price

				if moqs:
					vals['a_moq'] = vals['moq'] = moqs[0].min_qty
					vals['ar_code'] =vals['r_code'] = moqs[0].r_code
					vals['moq_id'] = moqs[0].id
					# vals['quote_price_unit'] = moqs[0].price_unit 

				if product.seller_ids:
					for sup in product.seller_ids:
						if sup.customer_id.id == self.order_id.partner_id.id:							
							vals['quote_price_unit'] = sup.sale_price
							vals['icon_sale_price']= sup.sale_price
							vals['price_unit']= sup.sale_price
							
							vals['product_uom_qty'] = sup.min_qty
							if sup.moq != 0:
								vals['moq'] = sup.moq
							if sup.delay != 0:
								vals['sale_delay'] = sup.delay
							if sup.product_name:
								vals['name'] = sup.product_name

				# if order_line:
				#     vals['quote_price_unit'] = order_line.price_unit
				# else:
				#     vals['quote_price_unit'] = vals['icon_sale_price'] #for get sale order
			# if self.company_id.is_forward_so:
				# self.markdown_discount = self.company_id.price_discount
			# vals['price_unit'] = 0
			# vals['quote_price_unit'] = 1.2
			# vals['sale_delay'] = 3
			# vals['packing_qty'] = 0
			self.update(vals)
		return res

	@api.onchange('product_id')
	def _onchange_product_id_set_customer_lead_icon(self):
		_trading_co_id = int(self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.trading_company_id', '3') or 0)
		if self.company_id.id == _trading_co_id:  # v16: replaced hardcoded 3 with ir.config_parameter
			self.customer_lead = int(self.product_id.custom_lead_time_by_weeks) * 7

	@api.onchange('product_uom',)
	def product_uom_change(self):
		res = super(SaleOrderLine, self).product_uom_change()
		_trading_co_id = int(self.env['ir.config_parameter'].sudo().get_param('iconnexion_custom.trading_company_id', '3') or 0)
		if self.company_id.id == _trading_co_id:  # v16: replaced hardcoded 3 with ir.config_parameter
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
				
				moqs = self.product_id.product_tmpl_id.moq_ids.filtered(lambda line: (line.product_variant_id==self.product_id or not line.product_variant_id) and line.min_qty<=self.product_uom_qty).sorted(key=lambda r: r.min_qty,reverse=True)
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
							vals['quote_price_unit'] = sup.sale_price
							vals['icon_sale_price']= sup.sale_price
							vals['price_unit']= sup.sale_price
							
							vals['product_uom_qty'] = sup.min_qty
							if sup.moq != 0:
								vals['moq'] = sup.moq
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

	@api.onchange('name')
	def product_cpn_icon_change(self):
		order_line = self.env['sale.order.line'].search([('product_id', '=', self.product_id.id),('name', '=', self.name), ('is_lower_margin', '=', False), ('order_id.partner_id', '=', self.order_id.partner_id.id)],limit=1)		 
				#What keith/stephy wants was to automate the U/P for existing orders
				#Same Customer , same MPN, same CPN, << system auto fill price with old price.
		if self.product_id.seller_ids:
			for sup in self.product_id.seller_ids:
				if sup.customer_id.id == self.order_id.partner_id.id:							
					self.quote_price_unit = sup.sale_price
					self.icon_sale_price = sup.sale_price
					self.price_unit = sup.sale_price					
					self.product_uom_qty = sup.min_qty
					self.moq = sup.moq
					

		if order_line:
			self.price_unit = order_line.quote_price_unit
			self.quote_price_unit = order_line.quote_price_unit
			self.icon_sale_price = order_line.quote_price_unit

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
				if self.is_special_price:
					if self.s_margin != 0:
						vals['is_lower_margin'] = True
					else:
						vals['is_lower_margin'] = False
				else: 
					if self.s_margin < margin:
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

					# cari ke semua part number, update product tersebut
					#davidsetiadi11


		self.update(vals)

				
	def _action_launch_stock_rule(self, previous_product_uom_qty=False):
		"""
		Launch procurement group run method with required/custom fields genrated by a
		sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
		depending on the sale order line product rule.
		"""
		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
		procurements = []
		context = self._context
		is_iconnexion = False
		is_pi_clear = False
		# context['sale_order_id'] = self.id
		for line in self:
			# if line.order_id.is_iconnexion == True and line.order_id.is_generate_proforma == True:
			# 	is_iconnexion = True
		   
			if context.get('payment_paid'):
				is_pi_clear = True

			if line.payment_state != 'not_paid':
				is_pi_clear = True

			line = line.with_company(line.company_id)
			if line.state != 'sale' or not line.product_id.type in ('consu','product'):
				continue
			qty = line._get_qty_procurement(previous_product_uom_qty)
			if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
				continue

			group_id = line._get_procurement_group()
			if not group_id:
				group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
				line.order_id.procurement_group_id = group_id
			else:
				# In case the procurement group is already created and the order was
				# cancelled, we need to update certain values of the group.
				updated_vals = {}
				if group_id.partner_id != line.order_id.partner_shipping_id:
					updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
				if group_id.move_type != line.order_id.picking_policy:
					updated_vals.update({'move_type': line.order_id.picking_policy})
				if updated_vals:
					group_id.write(updated_vals)

			values = line._prepare_procurement_values(group_id=group_id)
			product_qty = line.product_uom_qty - qty

			line_uom = line.product_uom
			quant_uom = line.product_id.uom_id
			product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
			procurements.append(self.env['procurement.group'].Procurement(
				line.product_id, product_qty, procurement_uom,
				line.order_id.partner_shipping_id.property_stock_customer,
				line.name, line.order_id.name, line.order_id.company_id, values))
		if procurements:
			
			if is_iconnexion and not is_pi_clear:#context.get('sale_confirm'):
				# and tt payment terms
				return True

			self.env['procurement.group'].run(procurements)
		return True
		
	def action_sale_popup_wizard(self):
		return {
			'type': 'ir.actions.act_window',
			'name': 'Input Reason',
			'res_model': 'icon.sale.popup.wizard',
			'view_mode': 'form',
			'target': 'new',
			'context': {'active_id': self._context.get('active_id'), 'active_model': self._context.get('active_model')},
		}

	#override from sale to allow quoted price unit
	@api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'quote_price_unit')
	def _compute_amount(self):
		"""
		Compute the amounts of the SO line.
		"""
		for line in self:
			price = (line.price_unit or line.quote_price_unit)  * (1 - (line.discount or 0.0) / 100.0)
			taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
			line.update({
				'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
				'price_total': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
			})
			if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
				line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])



class IconCommitteddateHistory(models.Model):
	_name = 'icon.committeddate.history'
	_description = "Icon committeddate History"
	_order = 'id desc'

	sale_line_committeddate_history_id = fields.Many2one('sale.order.line', 'SO Line')
	date = fields.Date('Date')
	change_reason = fields.Char('Reason')
