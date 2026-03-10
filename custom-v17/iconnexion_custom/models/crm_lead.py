import logging

from odoo import api, fields, models, tools, SUPERUSER_ID, _

from odoo.http import request
from odoo.addons.website.models import ir_http
from odoo.addons.http_routing.models.ir_http import url_for

import threading
from datetime import date, datetime, timedelta
from psycopg2 import sql

from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.addons.phone_validation.tools import phone_validation
from collections import OrderedDict, defaultdict
from dateutil.parser import parse


_logger = logging.getLogger(__name__)

class IconPipelineRemark(models.Model):
	_name = 'icon.pipeline.remark'
	_description = "Pipeline Remark"
	_order = 'id asc'
	_rec_name = "lead_id"


	part_id = fields.Many2one('odes.part',string='Pipeline')  # v16: track_visibility removed (tracking=False is the default)	
	lead_id = fields.Many2one('crm.lead', 'CRM Lead')
	date = fields.Date('Date',default=fields.Date.today())
	name = fields.Char('Name')
	remarks = fields.Text(string='Remarks')
	
	@api.model
	def default_get(self, fields):
		res = super(IconPipelineRemark, self).default_get(fields)
		active_ids = self.env.context.get('active_ids', [])
		context = dict(self._context or {})
		active_model = context.get('active_model')
		active_id = context.get('active_id')
		if active_model == 'odes.part':
			part_id = self.env['odes.part'].browse(active_id)
			if part_id.lead_id:
				res['lead_id'] = part_id.lead_id.id
		res['part_id'] = active_ids[0]	
		
		return res

	@api.model_create_multi
	def create(self, vals_list):
		context = dict(self._context or {})
		active_model = context.get('active_model')
		active_id = context.get('active_id')
		if active_model == 'odes.part':
			part_id = self.env['odes.part'].browse(active_id)
			part_id.write({'reason':'reason'})
		return super(IconPipelineRemark, self).create(vals_list)

	def write(self, vals):
		context = dict(self._context or {})
		active_model = context.get('active_model')
		active_id = context.get('active_id')
		if active_model == 'odes.part':
			part_id = self.env['odes.part'].browse(active_id)
			part_id.write({'reason':'reason'})
		# for lead in self:
		# 	# if 'odes_part_ids' in vals:
		# 	if 'stage_id' in vals:
		# 		new_value = vals['stage_id']
		res = super(IconPipelineRemark, self).write(vals)

		return res
		
class IconDesignInProgress(models.Model):
	_name = 'icon.design.in.progress'
	_description = "DIP"
	_order = 'id asc'
	

	# product = fields.Many2one(related="crm_icon_dip_id.product_id", string="Product", store=True)
	# products_id = fields.Many2one("odes.part", string='Product')
	product_id = fields.Many2one('product.product',string='Product',)
	# productss_id = fields.Many2one('odes.part',string='Product')
	# products_id = fields.Many2one(string= "Products", related="productss_id.product_id")
	bidding_id = fields.Many2one('iconnexion.lead.type', string='Bidding Status')  # v16: track_visibility removed (tracking=False is the default)
	design_id = fields.Many2one('iconnexion.lead.type', string='Design Status')  # v16: track_visibility removed (tracking=False is the default)
	technical_id = fields.Many2one('iconnexion.lead.type', string='Technical Status')  # v16: track_visibility removed (tracking=False is the default)
	trading_id = fields.Many2one('iconnexion.lead.type', string='Trading Status')  # v16: track_visibility removed (tracking=False is the default)
	crm_icon_dip_id = fields.Many2one('crm.lead', 'CRM Lead (Bidding)')
	crm_icon_dip2_id = fields.Many2one('crm.lead', 'CRM Lead (Bidding Status)')
	crm_icon_dip3_id = fields.Many2one('crm.lead', 'CRM Lead (Bidding History)')
	crm_icon_dip_design_id = fields.Many2one('crm.lead', 'CRM Lead (Design)')
	crm_icon_dip2_design_id = fields.Many2one('crm.lead', 'CRM Lead (Design Status)')
	crm_icon_dip3_design_id = fields.Many2one('crm.lead', 'CRM Lead (Design History)')
	crm_icon_dip_enquiry_id = fields.Many2one('crm.lead', 'CRM Lead (Technical)')
	crm_icon_dip2_enquiry_id = fields.Many2one('crm.lead', 'CRM Lead (Technical Status)')
	crm_icon_dip3_enquiry_id = fields.Many2one('crm.lead', 'CRM Lead (Technical History)')
	crm_icon_dip_trading_id = fields.Many2one('crm.lead', 'CRM Lead (Trading)')
	crm_icon_dip2_trading_id = fields.Many2one('crm.lead', 'CRM Lead (Trading Status)')
	crm_icon_dip3_trading_id = fields.Many2one('crm.lead', 'CRM Lead (Trading History)')
	status = fields.Char('Status')
	remark = fields.Char('Remarks')
	is_check  = fields.Char('chec')
	bidding_remark = fields.Char('Bidding Remarks')
	dip_notes = fields.Char('Notes')
	design_remark = fields.Char('Design Remarks')
	technical_remark = fields.Char('Technical Remarks')
	trading_remark = fields.Char('Trading Remarks')
	check_datetime = fields.Datetime('Remarks Date') #, default=fields.Datetime.now)
	bidding_status_datetime = fields.Datetime ('Status Date')
	design_status_datetime = fields.Datetime ('Design Status Date')
	technical_status_datetime = fields.Datetime ('Technical Status Date')
	trading_status_datetime = fields.Datetime ('Trading Status Date')

	@api.onchange('bidding_remark')
	def _onchange_bidding_remark(self):
		active_id = self._origin.crm_icon_dip_id.id     
		
		if self.bidding_remark:
			self.create({'crm_icon_dip3_id':active_id,
				'check_datetime': datetime.now(),
				'bidding_remark':self.bidding_remark,
				'product_id': self.product_id.id,
				})


	@api.onchange('design_remark')
	def _onchange_design_remark(self):
		active_id = self._origin.crm_icon_dip_design_id.id
		if self.design_remark:
			self.create({'crm_icon_dip3_design_id':active_id,
				'check_datetime': datetime.now(),
				'design_remark':self.design_remark,
				'product_id': self.product_id.id,
				})

	@api.onchange('technical_remark')
	def _onchange_technical_remark(self):
		active_id = self._origin.crm_icon_dip_enquiry_id.id
		if self.technical_remark:
			self.create({'crm_icon_dip3_enquiry_id':active_id,
				'check_datetime': datetime.now(),
				'technical_remark':self.technical_remark,
				'product_id': self.product_id.id,
				})

	@api.onchange('trading_remark')
	def _onchange_remark(self):
		active_id = self._origin.crm_icon_dip_trading_id.id
		if self.trading_remark:
			self.create({'crm_icon_dip3_trading_id':active_id,
				'check_datetime': datetime.now(),
				'trading_remark':self.trading_remark,
				'product_id': self.product_id.id,
				})

	@api.onchange('bidding_id')
	def _onchange_bidding_status(self):
		active_id = self._origin.crm_icon_dip_id.id #self._context.get('params')['id']
		
		if self.bidding_id:
			self.dip_notes = self.bidding_id.notes
			self.create({'crm_icon_dip2_id':active_id,
				'bidding_status_datetime': datetime.now(),
				'bidding_id':self.bidding_id.id,
				'product_id': self.product_id.id,
				})
		
	@api.onchange('design_id')
	def _onchange_design_status(self):
		active_id = self._origin.crm_icon_dip_design_id.id
		
		if self.design_id:
			self.dip_notes = self.design_id.notes
			self.create({'crm_icon_dip2_design_id':active_id,
				'design_status_datetime': datetime.now(),
				'design_id':self.design_id.id,
				'product_id': self.product_id.id,
				})

	@api.onchange('technical_id')
	def _onchange_technical_status(self):
		active_id = self._origin.crm_icon_dip_enquiry_id.id
		
		if self.technical_id:
			self.dip_notes = self.technical_id.notes
			self.create({'crm_icon_dip2_enquiry_id':active_id,
				'technical_status_datetime': datetime.now(),
				'technical_id':self.technical_id.id,
				'product_id': self.product_id.id,
				})

	@api.onchange('trading_id')
	def _onchange_trading_status(self):
		active_id = self._origin.crm_icon_dip_trading_id.id

		if self.trading_id:
			self.dip_notes = self.trading_id.notes
			self.create({'crm_icon_dip2_trading_id':active_id,
				'trading_status_datetime': datetime.now(),
				'trading_id':self.trading_id.id,
				'product_id': self.product_id.id,
				})

	
		

class IconnectionLeadType(models.Model):
	_name = "iconnexion.lead.type"
	_description = "iConnexion Lead Type"

	name = fields.Char(string='Name',  required=True)
	notes = fields.Char(string='Notes',  required=True)
	type = fields.Selection([('business', 'Business Type'), ('customer', 'Customer Type'), ('activity', 'Business activity'),
							('bidding', 'Bidding'), ('design', 'Design'), ('technical', 'Technical Enquiry'), ('trading', 'Trading')],string='Type')

class IconnectionProductType(models.Model):
	_name = "iconnexion.product.type"
	_description = "iConnexion Product Type"

	name = fields.Char(string='Name',  required=True)

class ProductTemplate(models.Model):
	_inherit = "product.template"

	icon_type_id = fields.Many2one("iconnexion.product.type",string="Item Type")

class Lead(models.Model):
	_inherit = "crm.lead"

	crm_icon_dip_ids = fields.One2many('icon.design.in.progress', 'crm_icon_dip_id', 'DIP Bidding')
	crm_icon_dip_design_ids = fields.One2many('icon.design.in.progress', 'crm_icon_dip_design_id', 'DIP Design')
	crm_icon_dip_enquiry_ids = fields.One2many('icon.design.in.progress', 'crm_icon_dip_enquiry_id', 'DIP Enquiry')
	crm_icon_dip_trading_ids = fields.One2many('icon.design.in.progress', 'crm_icon_dip_trading_id', 'DIP Trading')
	business_type_id = fields.Many2one('iconnexion.lead.type',string='Business Type')  # v16: track_visibility removed (tracking=False is the default)
	customer_type_id = fields.Many2one('iconnexion.lead.type',string='Customer Type')  # v16: track_visibility removed (tracking=False is the default)
	business_activity_id = fields.Many2one('iconnexion.lead.type',string='Business Activity')  # v16: track_visibility removed (tracking=False is the default)
	project_status_id = fields.Many2one('iconnexion.lead.type', string='iConnexion Project Status')  # v16: track_visibility removed (tracking=False is the default)
	# design_type_id = fields.Many2one('iconnexion.lead.type',string='Projec Status')  # v16: track_visibility removed (tracking=False is the default)
	# technical_type_id = fields.Many2one('iconnexion.lead.type',string='Projec Status')  # v16: track_visibility removed (tracking=False is the default)
	# trading_type_id = fields.Many2one('iconnexion.lead.type',string='Projec Status')  # v16: track_visibility removed (tracking=False is the default)
	dip_type = fields.Selection([('bidding','Bidding'),('design','Design'),('trading','Trading'),('technical','Technical Enquiry')],string="Category")
	is_required_dip = fields.Boolean('Required DIP')
	dip_type_fill = fields.Char('Type DIP') 
	crm_bidding_history_ids = fields.One2many("icon.design.in.progress", "crm_icon_dip3_id", "Bidding History")
	crm_design_history_ids = fields.One2many("icon.design.in.progress", "crm_icon_dip3_design_id", "Design History")
	crm_technical_history_ids = fields.One2many("icon.design.in.progress", "crm_icon_dip3_enquiry_id", "Technical Enquiry History")
	crm_trading_history_ids = fields.One2many("icon.design.in.progress", "crm_icon_dip3_trading_id", "Trading History")
	crm_bidding_status_history_ids = fields.One2many("icon.design.in.progress", "crm_icon_dip2_id", "Bidding Status History")
	crm_design_status_history_ids = fields.One2many("icon.design.in.progress", "crm_icon_dip2_design_id", "Design Status History")
	crm_technical_status_history_ids = fields.One2many("icon.design.in.progress", "crm_icon_dip2_enquiry_id", "Technical Status History")
	crm_trading_status_history_ids = fields.One2many("icon.design.in.progress", "crm_icon_dip2_trading_id", "Trading Enquiry History")
	req_new_part_number_ids = fields.One2many("req.new.part.number.wizard", "req_new_part_number_id", "Req New Part Number")
	sample_qty = fields.Float('Sample Qty', compute='_compute_sample_qty')
	received_date =fields.Date('Received', compute='_compute_received_date')
	given_date =fields.Date('Given', compute='_compute_given_date')
	engagement_date =fields.Date('Engagement Date',default=fields.Date.today())
	end_partner_char = fields.Char(string='End Customer (Text)')

	is_iconnexion = fields.Boolean(string="iConnexion Company", compute='compute_is_iconnexion', store=True)
	state_approval = fields.Selection([('approval', 'Approval'), ('approved', "Approved")], string="Approval State")
	contact_id = fields.Many2one("res.partner", "Contacts")
	sample_request_count = fields.Integer('# Sample Request', compute='_compute_sample_request')
	partner_id = fields.Many2one(
		'res.partner', string='Customer', index=True, tracking=10,
		domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
		help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")
	remarks_ids = fields.One2many('icon.pipeline.remark','lead_id','Remarks')
	
	email_from = fields.Char(
		'Email', tracking=40, index=True,
		compute='_compute_email_from', inverse='_inverse_email_from', readonly=False, store=True)
	phone = fields.Char(
		'Phone', tracking=50,
		compute='_compute_phone', inverse='_inverse_phone', readonly=False, store=True)


	def handle_partner_assignment(self, force_partner_id=False, create_missing=True):
		""" Update customer (partner_id) of leads. Purpose is to set the same
		partner on most leads; either through a newly created partner either
		through a given partner_id.

		:param int force_partner_id: if set, update all leads to that customer;
		:param create_missing: for leads without customer, create a new one
			based on lead information;
		"""
		for lead in self:
			if force_partner_id:
				lead.partner_id = force_partner_id
			if not lead.partner_id and create_missing:
				partner = lead._create_customer()
				lead.partner_id = partner.parent_id.id
				lead.contact_id = partner.id


	def _compute_sample_qty(self):
		for i in self:
			quantity = 0
			sample_obj_ids = self.env['sample.request.form'].search([('crm_id', '=', i.id)], order='id DESC')
			for sample in sample_obj_ids:				
				picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'),('company_id','=',self.company_id.id)], order='id DESC')
				for pickings in picking_type:
					stock_picking = self.env['stock.picking'].search([('picking_type_id', '=', pickings.id,), ('state', '=', 'done'), ('sample_request_id', '=', sample.id ), ('origin', '=', sample.name )], order='id DESC')
					for stocks in stock_picking:
						for stocklines in stocks.move_ids_without_package:
							quantity += stocklines.quantity_done
			
			i.sample_qty = quantity
			


	def _compute_received_date(self):
		for i in self:
			sample_receive = self.env['sample.request.form'].search([('crm_id', '=', i.id)], order='id DESC', limit=1)
			i.received_date = sample_receive.received_date


	def _compute_given_date(self):
		for i in self:
			sample_given = self.env['sample.request.form'].search([('crm_id', '=', i.id)], order='id DESC', limit=1)
			i.given_date = sample_given.given_date

	@api.model
	def search(self, args, offset=0, limit=None, order=None, count=False):
		context = self._context
		ctx = {'disable_search': True}
		# if self._context.get('disable_search'): 
		
		if ctx.get('disable_search'):
			if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_hod') or self.user_has_groups('odes_crm.group_odes_customer'):
				return super(Lead, self).search(args, offset=offset, limit=limit, order=order, count=count)
			
			report_to_user_ids = self.env.user.report_to_user_crm_ids
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
		res = super(Lead, self).search(args, offset=offset, limit=limit, order=order, count=count)
		return res

	@api.model
	def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
		ctx = {'disable_search': True}
		# if self._context.get('disable_search'):  
		if ctx.get('disable_search'):
			if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_hod') or self.user_has_groups('odes_crm.group_odes_customer'):
				return super(Lead, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
  
			report_to_user_ids = self.env.user.report_to_user_crm_ids
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

		res = super(Lead, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
		return res

	@api.constrains('stage_id')
	def _check_stages(self):
		sale_obj = self.env['sale.order']
		for lead in self:
			if lead.stage_id.is_need_so:
				order1 = sale_obj.search([('opportunity_id', '=', lead.id), ('state', '!=', 'cancel')], limit=1)
				if not order1:
					raise ValidationError(_('Please input a Quotation to change the stage into "%s".') % (lead.stage_id.name))
			if lead.stage_id.is_confirm_so and not lead.is_iconnexion:
				order2 = sale_obj.search([('opportunity_id', '=', lead.id), ('state', 'in', ('sale', 'done'))], limit=1)
				if not order2:
					raise ValidationError(_('Please confirm the Quotation to change the stage into "%s".') % (lead.stage_id.name))

	def action_view_sale_quotation(self):
		res = super(Lead, self).action_view_sale_quotation()
		contact_id = False
		if self.contact_id:
			contact_id = self.contact_id.id

		res['context'] = {
			'search_default_partner_id': self.partner_id.id,
			'default_partner_id': self.partner_id.id,
			'default_opportunity_id': self.id,
			'default_is_current': 1,
			'search_default_is_current': 1,
			'default_contact_id': contact_id,
			'default_pricelist_id': self.partner_id.property_product_pricelist.id,
			# 'default_so_type': 'sf',
		}
		
		return res


	def action_schedule_meeting(self):
		""" Open meeting's calendar view to schedule meeting on current opportunity.
			:return dict: dictionary value for created Meeting view
		"""
		self.ensure_one()
		action = self.env["ir.actions.actions"]._for_xml_id("calendar.action_calendar_event")
		partner_ids = self.env.user.partner_id.ids
		if self.partner_id:
			partner_ids.append(self.partner_id.id)
		# partner_id =
		if self.is_iconnexion:
			partner_ids = partner_ids = self.env.user.partner_id.ids

		action['context'] = {
			'default_opportunity_id': self.id if self.type == 'opportunity' else False,
			'default_partner_id': self.partner_id.id,
			'default_partner_ids': partner_ids,
			'default_team_id': self.team_id.id,
			'default_name': self.name,
		}
		return action


	def _compute_sample_request(self):
		for crm_lead in self:
			crm_lead.sample_request_count = self.env['sample.request.form'].search_count(
				[('crm_id', '=', self.id)])

	def button_sample_request(self):
		return {
			'name': _('iConnexion'),
			'res_model': 'sample.request.wizard',
			'view_mode': 'form',
			'type': 'ir.actions.act_window',
			'target':'new',
			}
			
	def get_sample_request(self):
		self.ensure_one()

		data_product = []
		for data in self.odes_part_ids:
			if data.manufacture not in data_product:
				data_product.append(data.manufacture)
			# id_product = self.env['product.product'].search([('product_id','=',data.manufacture)])
			# data_product.append(id_product.id)
			# print("data_product::::",data_product) #comment code due error, check by david 13042022
		if self.id:
			for brand in data_product:
				product_line = []
				for data in self.odes_part_ids:
					if data.manufacture == brand:
						product_line.append([0, 0, {
								'product_id': data.product_id.id,
								'qty': 0,
							}])
				self.env['sample.request.form'].create({'crm_id':self.id,
													'partner_id': self.partner_id.id,
													'opportunity_id': self.id,
													'user_id': self.user_id.id,
													'company_id': self.company_id.id or self.env.company.id,
													'contact_id': self.contact_id.id,
													'email': self.email_from,
													'telephone': self.phone,
													'prototype_quantity': self.pilot_qty,
													'aplication': self.application_id.name,
													'project_name': self.project_name,
													'project_desc': self.end_product_display_name,
													'quantity_1': self.annual_qty,
													'quantity_2': self.annual_qty,
													'project_reference_no': self.name,
													'production_start_date': self.pilot_schedule_date,
													'project_start_date': self.pilot_schedule_date,
													'product_line' : product_line,
											})

		return {
			'type': 'ir.actions.act_window',
			'name': 'Sample Request',
			'view_mode': 'tree,form',
			'res_model': 'sample.request.form',
			'domain': [('crm_id', '=', self.id)],
			'context': {'default_crm_id':self.id,
						'default_partner_id': self.partner_id.id,
						'default_opportunity_id': self.id,
						'default_user_id': self.user_id.id,
						'default_company_id': self.company_id.id or self.env.company.id,
						'default_aplication': self.application,
						'default_project_name': self.project_name,
						'default_project_desc': self.end_product_display_name,
						'default_project_start_date': self.pilot_schedule_date,
						'form_view_ref': 'iconnexion_custom.sample_request_form_view_form', 
						'tree_view_ref':'iconnexion_custom.sample_request_form_view_tree'}
		}

	def action_sample_request(self):
		return self.env["ir.actions.actions"]._for_xml_id("iconnexion_custom.action_sample_request_form")

	@api.depends('company_id')
	def compute_is_iconnexion(self):
		for lead in self:
			company_name = lead.company_id.name
			if company_name and 'iconnexion' in company_name.lower():
				lead.is_iconnexion = True
			else:
				lead.is_iconnexion = False
	
	@api.onchange('partner_id')
	def onchange_icon_partner_id(self):
		"""
		Update the following fields when the partner is changed:
		- Pricelist
		- Payment terms
		- Invoice address
		- Delivery address
		"""
		if not self.partner_id:
			self.update({
				'contact_id': False,
			})
		

	def write(self, vals):
		context = dict(self._context or {})
		for lead in self:
			if self.odes_part_ids:
				total_pot = 0.0
				potential = 0.0
				for x in self.odes_part_ids:
					if 'annual_qty' in vals:
						annual_qty = vals['annual_qty']
						potential = x.quoted_price * annual_qty
						total_pot += potential
						lead.write({'currency_revenue' : total_pot})
			# if 'odes_part_ids' in vals:
			if 'stage_id' in vals:
				new_value = vals['stage_id']
				new_value_search = self.env['crm.stage'].browse(new_value)
				new_values = new_value_search.name
			
				new_sequence = new_value_search.sequence
				old_sequence = lead.stage_id.sequence
				if lead.is_iconnexion:
					if new_sequence != old_sequence and not context.get('icon_view'):
						raise UserError(_('Sorry, you cannot move the Stage.\nPlease use the "iConnexion Flow" .'))


				if new_values == 'DIP':
				# if vals['odes_part_ids']:
					vals['is_required_dip'] = True
					odes_dip_obj = self.env['icon.design.in.progress']
					odes_dip_ids = odes_dip_obj.search([('crm_icon_dip_id','=',self.id)])
					odes_dip_ids.unlink()
					# dip_create_list = [{
					#   'crm_icon_dip_id': self.id, 
					#   'status': 'Bidding: DIP- This is bidding project'
					#   },{
					#   'crm_icon_dip_id': self.id, 
					#   'status': 'Bidding: L1 - iConnexion pricing in L1'
					#   },{
					#   'crm_icon_dip_id': self.id, 
					#   'status': 'Bidding: Order Win'
					#   },{
					#   'crm_icon_dip_id': self.id, 
					#   'status': 'Bidding: Order Lost'
					#   }]
					dip_create_list = []
					for part in lead.odes_part_ids:

						dip_create_list.append({
						'crm_icon_dip_id': self.id, 
						'status': 'Bidding: DIP- This is bidding project',
						'product_id': part.product_id.id,
						})
					odes_dip_obj.create(dip_create_list)
					#design
					odes_dip_ids = odes_dip_obj.search([('crm_icon_dip_design_id','=',self.id)])
					odes_dip_ids.unlink()
					dip_create_list = []
					for part in lead.odes_part_ids:

						dip_create_list.append({
						'crm_icon_dip_design_id': self.id, 
						'status': 'Design: Prospect - There is potential project',
						'product_id': part.product_id.id,
						})
					
					
					odes_dip_obj.create(dip_create_list)
					# #enquiry
					odes_dip_ids = odes_dip_obj.search([('crm_icon_dip_enquiry_id','=',self.id)])
					odes_dip_ids.unlink()
					dip_create_list = []
					for part in lead.odes_part_ids:

						dip_create_list.append({
						'crm_icon_dip_enquiry_id': self.id, 
						'status': 'Technical Enquiry',
						'product_id': part.product_id.id,
						})
						
					
					odes_dip_obj.create(dip_create_list)

					odes_dip_ids = odes_dip_obj.search([('crm_icon_dip_trading_id','=',self.id)])
					odes_dip_ids.unlink()
					dip_create_list = []
					for part in lead.odes_part_ids:

						dip_create_list.append({
						'crm_icon_dip_trading_id': self.id, 
						'status': 'Trading',
						'product_id': part.product_id.id,
						})
					#   },{
					#   'crm_icon_dip_trading_id': self.id, 
					#   'status': 'Order Win'
					#   },{
					#   'crm_icon_dip_trading_id': self.id, 
					#   'status': 'Order Lost'
					#   }]
					
					odes_dip_obj.create(dip_create_list)

			if 'project_status_id' in vals:				
				project_status_id = self.env['iconnexion.lead.type'].browse(vals['project_status_id'])
				if project_status_id:						
					if project_status_id.name == 'Order Win':						
						if lead.stage_id.name == 'DIP' and lead.is_iconnexion:
							proposal_stage_id = self.env['crm.stage'].search([('name','=','Design Win')])
							if proposal_stage_id:								
								 vals['stage_id'] = proposal_stage_id.id

		res = super(Lead, self).write(vals)

		return res

	@api.onchange('dip_type')
	def _onchage_dip_type(self):
		if self.dip_type:
			self.dip_type_fill = self.dip_type

	# @api.onchange('project_status_id')
	# def _onchage_project_status_id(self):
	# 	if self.project_status_id:
	# 		if self.project_status_id.name == 'Order Win':
	# 			if self.stage_id.name == 'DIP' and self.is_iconnexion:
	# 				proposal_stage_id = self.env['crm.stage'].search([('name','=','Design Win')])
	# 				if proposal_stage_id:
	# 					self.with_context({'icon_view': 1,}).write({'stage_id': proposal_stage_id.id})

	def action_set_won_rainbowman(self):
		res = super(Lead, self).action_set_won_rainbowman()
		for lead in self:
			#find lost rewrite and find wond check box
			odes_dip_obj = self.env['icon.design.in.progress']
			odes_dip_ids = odes_dip_obj.search([('status','=','Bidding: Order Win'),('crm_icon_dip_id','=',self.id)])
			odes_dip_ids.write({'remark':True, 'check_datetime':datetime.now()})
			odes_dip2_ids = odes_dip_obj.search([('status','=','Design: Order Win'),('crm_icon_dip_design_id','=',self.id)])
			odes_dip2_ids.write({'remark':True, 'check_datetime':datetime.now()})
			odes_dip3_ids = odes_dip_obj.search([('status','=','Order Win'),('crm_icon_dip_trading_id','=',self.id)])
			odes_dip3_ids.write({'remark':True, 'check_datetime':datetime.now()})
		return res

	def toggle_active(self):
		""" When archiving: mark probability as 0. When re-activating
		update probability again, for leads and opportunities. """
		res = super(Lead, self).toggle_active()
		
		odes_dip_obj = self.env['icon.design.in.progress']
		odes_dip_ids = odes_dip_obj.search([('status','=','Bidding: Order Win'),('crm_icon_dip_id','=',self.id)])
		odes_dip_ids.write({'remark':False})
		odes_dip2_ids = odes_dip_obj.search([('status','=','Design: Order Win'),('crm_icon_dip_design_id','=',self.id)])
		odes_dip2_ids.write({'remark':False})
		odes_dip3_ids = odes_dip_obj.search([('status','=','Order Win'),('crm_icon_dip_trading_id','=',self.id)])
		odes_dip3_ids.write({'remark':False})
		odes_dip_obj = self.env['icon.design.in.progress']
		odes_dip_ids = odes_dip_obj.search([('status','=','Bidding: Order Lost'),('crm_icon_dip_id','=',self.id)])
		odes_dip_ids.write({'remark':False})
		odes_dip2_ids = odes_dip_obj.search([('status','=','Design: Order Lost'),('crm_icon_dip_design_id','=',self.id)])
		odes_dip2_ids.write({'remark':False})
		odes_dip3_ids = odes_dip_obj.search([('status','=','Order Lost'),('crm_icon_dip_trading_id','=',self.id)])
		odes_dip3_ids.write({'remark':False})
		return res

	def convert_opportunity_approve(self, partner_id, user_ids=False, team_id=False, ):
		customer = False
		if partner_id:
			customer = self.env['res.partner'].browse(partner_id)
		for lead in self:
			if not lead.active or lead.probability == 100:
				continue
			vals = lead._convert_opportunity_data(customer, team_id)
			
			lead.write(vals)
			if lead.is_iconnexion:
				lead.write({'type': 'lead',
				'state_approval': 'approval'})

		if user_ids or team_id:
			self.handle_salesmen_assignment(user_ids, team_id)

		return True

	def approve_new_customer_lead(self):
		self.write({
			'type': 'opportunity',
			'state_approval': 'approved',
			})

	@api.depends('partner_id.email', 'contact_id.email', 'partner_id', 'contact_id')
	def _compute_email_from(self):
		for lead in self:
			if lead.contact_id and lead.is_iconnexion:
				if lead.contact_id.email and lead.contact_id.email != lead.email_from:
					lead.email_from = lead.contact_id.email
				if lead.contact_id.email == False :
					if lead.email_from:
						lead.email_from = False
			else: 
				if lead.partner_id.email and lead.partner_id.email != lead.email_from:
					lead.email_from = lead.partner_id.email
				if lead.partner_id.email == False:
					lead.email_from = False
					
	def _inverse_email_from(self):
		for lead in self:
			if not lead.is_iconnexion:
				if lead.partner_id and lead.email_from != lead.partner_id.email:
					lead.partner_id.email = lead.email_from

	@api.depends('partner_id.phone', 'contact_id.phone', 'partner_id', 'contact_id')
	def _compute_phone(self):
		for lead in self:
			if lead.contact_id and lead.is_iconnexion:
				if lead.contact_id.phone and lead.phone != lead.contact_id.phone:
					lead.phone = lead.contact_id.phone
				if lead.contact_id.phone == False :
					lead.phone = False
			else:
				if lead.partner_id.phone and lead.phone != lead.partner_id.phone:
					lead.phone = lead.partner_id.phone
				if lead.partner_id.phone == False:
					lead.phone = False

	def _inverse_phone(self):
		for lead in self:
			if not lead.is_iconnexion:
				if lead.partner_id and lead.phone != lead.partner_id.phone:
					lead.partner_id.phone = lead.phone

class OdesPart(models.Model):
	_inherit = "odes.part"
	
	competitor_information = fields.Char('Competitor')
	competitor_price = fields.Float('Competitor Price / Target Price')
	quoted_price = fields.Float('Quoted Price',digits='Product Price')
	item_quantity = fields.Float('Item Quantity')
	competitor_mpn = fields.Char('Competitor MPN')
	competitor_pricing = fields.Char('Competitor Pricing')
	competitor_moq = fields.Char('Competitor MOQ')
	# icon_date = fields.Date('Date',default=fields.Datetime.now)
	icon_date = fields.Date(related='lead_id.engagement_date',string="Date",store=False)
	#modified david 31 05 2022
	user_id_rel = fields.Many2one('res.users', related='lead_id.user_id',string="Salesperson",store=True)
	stage_id_rel = fields.Many2one('crm.stage', related='lead_id.stage_id',string="CRM Stage",store=True)
	customer_name_rel = fields.Many2one('res.partner', related='lead_id.partner_id',string="Customer Name",store=True)
	contact_name_rel = fields.Many2one('res.partner', related='lead_id.contact_id',string="Contact Name",store=True)
	contact_number_rel = fields.Char(related='lead_id.phone',string="Contact Number",store=True)
	contact_email_rel = fields.Char(related='lead_id.email_from',string="Contact Email",store=True)	
	application_rel = fields.Many2one('odes.application', related='lead_id.application_id',string="Application",store=True)
	project_name_rel = fields.Char(related='lead_id.project_name',string="Project Name",store=True)
	deu = fields.Float(related='lead_id.annual_qty',string="EAU")
	total_potential = fields.Float('Total Potential', compute='_compute_total_potential',store=True)
	remarks = fields.Char('Remarks (Char)')
	reason = fields.Char('Reason (Char)')
	remarks_ids = fields.One2many('icon.pipeline.remark','part_id','Remarks')
	last_remark_date = fields.Date(compute='_compute_last_remark', string='Last Remark Date')
	last_remark = fields.Char(compute='_compute_last_remark', string='Last Remark') 
	customer_type_id =  fields.Many2one('iconnexion.lead.type', related='lead_id.customer_type_id',string="Customer Type",store=True)
	last_reason = fields.Char(compute='_compute_last_remark', string='Last Reason') 
	is_show_on_dashboard = fields.Boolean('Show On Dashboard',default=True)
	# is_iconnexion = fields.Boolean(string="iConnexion Company", related='lead_id.is_iconnexion', store=True)
	# last update by
	# ambil nilai harga quotation terakhir klo ada
	quoted_price_2 = fields.Float('Quoted Unit Price',digits='Product Price', compute='_compute_quote_unit_price')

	def _compute_quote_unit_price(self):
		for part in self:
			
			part.quoted_price_2 = part.quoted_price		

			order_id =  self.env['sale.order'].search([('opportunity_id','=',part.lead_id.id)],limit=1)
			if order_id and part.product_id:
				line_ids =  self.env['sale.order.line'].search([('product_id','=',part.product_id.id),('order_id','=',order_id.id)],limit=1)
				if line_ids:
					part.quoted_price_2 = line_ids.quote_price_unit

			# sql_query = """ select distinct on (p.id) p.id from res_partner p
			# 											left join mail_channel_partner mcp on p.id = mcp.partner_id
			# 											left join mail_channel c on c.id = mcp.channel_id
			# 											left join res_users u on p.id = u.partner_id
			# 													where (u.notification_type != 'inbox' or u.id is null)
			# 													and (p.email != ANY(%s) or p.email is null)
			# 													and c.id = ANY(%s)
			# 													and p.id != ANY(%s)"""

			# self.env.cr.execute(sql_query, (([email_from], ), (email_cids, ), (exept_partner, )))
			# for partner_id in self._cr.fetchall():



	def _compute_last_remark(self):
		for part in self:
			date = ''
			remarks = ''
			reason = ''
			for remark in part.remarks_ids:
				date = remark.date
				info = (remark.remarks[:20] + '..') if len(remark.remarks) > 20 else remark.remarks
				remarks = info
			if part.lead_id:
				for reason in part.lead_id.odes_stage_ids:
					reason = reason.backward_reason 

			part.last_remark_date = date
			part.last_remark = remarks
			part.last_reason = reason

	# show Customer Name, Application, Project Name & DEU, Total Potential (DEU * Quoted Price), Remarks & Edit Stage BUtton (Allow to Change CRM Stage & Remarks)
	@api.depends('lead_id','lead_id.annual_qty','quoted_price')
	def _compute_total_potential(self):
		for part in self:
			part.total_potential = part.lead_id.annual_qty * part.quoted_price


	@api.onchange('product_id')
	def onchange_product_id(self):
		for rec in self:
			rec.name = rec.product_id.default_code
			rec.manufacture = rec.product_id.product_brand_id.name
			rec.price = rec.product_id.standard_price
			rec.quoted_price = rec.product_id.product_tmpl_id.list_price

	# ii. Proposal : User add products after create user when state stage new and type opportunity

	@api.model_create_multi
	def create(self, vals_list):
		context = dict(self._context or {})
		if context.get('default_type') == 'opportunity':
			for vals in vals_list:
				if 'lead_id' in vals:
					lead_id = self.env['crm.lead'].browse(vals['lead_id'])
					if lead_id:
						if lead_id.stage_id.name == 'New' and lead_id.is_iconnexion:
							proposal_stage_id = self.env['crm.stage'].search([('name','=','Proposal')])
							if proposal_stage_id:
								lead_id.with_context({'icon_view': 1,}).write({'stage_id': proposal_stage_id.id})
						total_pot = 0.0
						potential = 0.0
						grand_total = 0.0
						for x in lead_id.odes_part_ids:
							total_pot += x.total_potential
						potential = vals['quoted_price'] * lead_id.annual_qty
						grand_total = total_pot + potential
						lead_id.with_context({'icon_view': 1,}).write({'currency_revenue': grand_total})

		return super().create(vals_list)
		
	def write(self, vals):
		context = dict(self._context or {})
		
		if context.get('default_type') == 'opportunity':
			if 'lead_id' in self:
				lead_id = self.env['crm.lead'].browse(self['lead_id'])
				if lead_id:
					total_pot = 0.0
					potential = 0.0
					current_pot = 0.0
					grand_total = 0.0
					for x in self.lead_id.odes_part_ids:
						current_pot += x.total_potential
					potential = self.quoted_price * self.lead_id.annual_qty
					if 'quoted_price' in vals:
						total_pot = vals['quoted_price'] * self.lead_id.annual_qty
						grand_total = current_pot - potential + total_pot
						self['lead_id'].with_context({'icon_view': 1,}).write({'currency_revenue': grand_total})
					
		res = super(OdesPart, self).write(vals)

		return res

	def unlink(self):
		context = dict(self._context or {})
		if context.get('default_type') == 'opportunity':
			if 'lead_id' in self:
				lead_id = self.env['crm.lead'].browse(self['lead_id'])

				if lead_id:
					total_pot = self.lead_id.currency_revenue
					potential = 0.0				
					for x in self:
						potential += x.quoted_price * x.lead_id.annual_qty

					grand_total = total_pot - potential
					self['lead_id'].with_context({'icon_view' : 1,}).write({'currency_revenue' : grand_total})

		res = super(OdesPart, self).unlink()

		return res
		
