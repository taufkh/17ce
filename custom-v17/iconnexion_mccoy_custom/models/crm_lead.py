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
	_inherit = 'icon.pipeline.remark'


class CrmLead(models.Model):
	_inherit = 'crm.lead'
	
	design_owner_id = fields.Many2one('res.users', string='Design Owner', tracking=True)
	is_mccoy = fields.Boolean(string="McCoy Company", compute='compute_is_mccoy', store=True)
	annual_qty = fields.Float('Annual Qty', default=None)
	product_id = fields.Many2one('product.product', 'Product', related='odes_part_ids.product_id', readonly=True)
	email_from = fields.Char(
		string='Email *', tracking=40, index=True,
		compute='_compute_email_from', inverse='_inverse_email_from', readonly=False, store=True)
	phone = fields.Char(
		string='Phone *', tracking=50,
		compute='_compute_phone', inverse='_inverse_phone', readonly=False, store=True)

	# design_owner_prepare_id = fields.Many2one('res.users', string='Design Owner Prepare')
	# reason_change_design_owner = fields.Char(string='Reason Change Design Owner')	

	def action_apply_lost_stage(self):
		return {
			'name': 'Lost Reason',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'odes.crm.backward.stage.wizard',
			'target': 'new',
			'context': {'action_lost': True},
		}

	def onwrite_stage_id(self):
		context = dict(self._context or {})
		odes_stage_obj = self.env['odes.crm.stage']
		if self.odes_stage_ids:
			last_stage = odes_stage_obj.search([('lead_id', '=', self.id)], order='id desc', limit=1)
			last_stage.end_datetime = datetime.now()
			odes_stage_obj.create({'lead_id': self.id, 'stage_name': self.stage_id.name})
		else:
			odes_stage_obj.create({'lead_id': self.id, 'stage_name': self.stage_id.name})

	def action_view_sale_quotation(self):
		quotations = self.env['sale.order'].search([('opportunity_id', '=', self.id)], order='id DESC')
		action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
		if len(quotations) > 1:
			action['domain'] = [('id', 'in', quotations.ids)]
		elif len(quotations) == 1:
			form_view = [(self.env.ref('sale.view_order_form').id, 'form')]
			if 'views' in action:
				action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
			else:
				action['views'] = form_view
			action['res_id'] = quotations.id
		else:
			action['domain'] = [('id', 'in', quotations.ids)]


		context = {
			'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id
		}
		action['context'] = context
		return action

	@api.onchange('email_from', 'phone')
	def _onchange_email_phone(self):
		for lead in self:
			if (lead.is_iconnexion or lead.is_mccoy) and lead.contact_id:
				if lead.contact_id.email != lead.email_from:
					lead.email_from = None
					raise ValidationError('Please click the box next to "Contacts" to enter the email.')
				if  lead.contact_id.phone != lead.phone:
					lead.phone = None
					raise ValidationError('Please click the box next to "Contacts" to enter the phone number.')
				

	@api.onchange('contact_id')
	def _onchange_contact_id(self):
		for lead in self:
			if (lead.is_iconnexion or lead.is_mccoy) and lead.contact_id:
				lead.email_from = lead.contact_id.email 
				lead.phone = lead.contact_id.phone 
			if (lead.is_iconnexion or lead.is_mccoy) and not lead.contact_id:
				lead.email_from = ''
				lead.phone = ''

	@api.constrains('annual_qty', 'odes_part_ids')
	def _restriction_annual_qty(self):
		for lead in self:
			if (lead.is_mccoy or lead.is_iconnexion) and lead.annual_qty < 1:
				raise ValidationError('Annual Qty cannot be %s.' % lead.annual_qty)


	@api.depends('company_id')
	def compute_is_mccoy(self):
		for lead in self:
			company_name = lead.company_id.name
			if company_name and 'mccoy' in company_name.lower():
				lead.is_mccoy = True
			else:
				lead.is_mccoy = False

	#groups field
	is_group_iconnexion_design_owner_manager = fields.Boolean(string='Design Owner Manager', compute='_compute_is_in_group')

	#group function
	def _compute_is_in_group(self):
		for leads in self:
			if self.user_has_groups('iconnexion_mccoy_custom.group_iconnexion_design_owner_manager'):
				leads.is_group_iconnexion_design_owner_manager = True
			else:
				leads.is_group_iconnexion_design_owner_manager = False

	@api.constrains('design_owner_id')
	def _change_design_owner_in_lead(self):
		odes_part_obj = self.env['odes.part']
		for lead in self:
			odes_parts = odes_part_obj.search([('lead_id', '=', lead.id)])
			for part in odes_parts:
				part.write({'design_owner_id': lead.design_owner_id.id})

	# @api.constrains('design_owner_prepare_id', 'reason_change_design_owner')
	# def _check_reason_change_design_owner(self):
	# 	for lead in self:
	# 		if lead.design_owner_prepare_id:
	# 			partner_ids = []
	# 			group = self.env.ref('iconnexion_mccoy_custom.group_iconnexion_design_owner_approve_button')
	# 			group_users = self.env['res.users'].search([('groups_id', 'in', group.id)])
	# 			for user in group_users:
	# 				partner_ids.append(user.partner_id.id)
	# 			if partner_ids:
	# 				lead.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
	# 						'iconnexion_mccoy_custom.design_owner_approval_notification',
	# 						values={'lead': lead,},
	# 						subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
	# 						partner_ids=partner_ids,notify = False,
	# 						subject='Approval of '+ lead.name,                            
	# 					)
	# 		if lead.design_owner_id and lead.design_owner_prepare_id and not lead.reason_change_design_owner:
	# 			raise ValidationError('Please provide a reason for changing the Design Owner.')

	# def approve_change_design_owner(self):
	# 	for lead in self:
	# 		lead.design_owner_id = lead.design_owner_prepare_id
	# 		lead.design_owner_prepare_id = False
	# 		lead.reason_change_design_owner = False
	
	

class OdesPart(models.Model):
	_inherit = 'odes.part'


	design_owner_id = fields.Many2one('res.users', string='Design Owner')
	last_remark_date = fields.Date(compute='_compute_last_remark', string='Last Remark Date', store=True)
	last_remark = fields.Char(compute='_compute_last_remark', string='Last Remark', store=True)
	last_reason = fields.Char(compute='_compute_last_remark', string='Last Reason', store=True) 
	no_of_per = fields.Float(string='No of PER')
	quoted_price_2 = fields.Float('Quoted Unit Price',digits='Product Price', compute='_compute_quote_unit_price', compute_sudo=True)
	is_odes = fields.Boolean(string='Odes Company', related='lead_id.is_odes', store=True)
	is_show_on_dashboard = fields.Boolean('Show On Dashboard',default=False, copy=False)
	is_show_on_dashboard_rel = fields.Boolean('Show On Dashboard (Readonly)', related='is_show_on_dashboard')
	phone_rel = fields.Char(string="Phone", related="lead_id.phone", store=True)
	source_rel = fields.Selection(related='lead_id.source', string='Source', readonly=True, store=True)
	sales_team_id_rel = fields.Many2one(related='lead_id.team_id', string='Sales Team', readonly=True, store=True)
	date_deadline_rel = fields.Date(related='lead_id.date_deadline', string='Expected Closing', readonly=True, store=True)
	priority_rel = fields.Selection(related='lead_id.priority', string='Priority', readonly=True, store=True)
	stage_latest_update_rel = fields.Integer(related='lead_id.stage_latest_update', string='Latest Update Days', readonly=True, store=True)
	company_id_rel = fields.Many2one(related='lead_id.company_id', string='Company', readonly=True, store=True)
	end_partner_char_rel = fields.Char(related='lead_id.end_partner_char', string='End Customer', readonly=True, store=True)
	end_product_display_name_rel = fields.Char(related='lead_id.end_product_display_name', string='End Product', readonly=True, store=True)
	contract_site_rel = fields.Char(related='lead_id.contract_site', string='Contract Manufacturing', readonly=True, store=True)
	design_location_rel = fields.Char(related='lead_id.design_location', string='Design Location', readonly=True, store=True)
	annual_qty_rel = fields.Float(related='lead_id.annual_qty', string='Annual Qty', readonly=True, store=True)
	mass_schedule_date_rel = fields.Date(related='lead_id.mass_schedule_date', string='Mass Production Schedule', readonly=True, store=True)
	pilot_qty_rel = fields.Float(related='lead_id.pilot_qty', string='Pilot Run Qty', readonly=True, store=True)
	pilot_schedule_date_rel = fields.Date(related='lead_id.pilot_schedule_date', string='Pilot Run Schedule Date', readonly=True, store=True)
	dip_type_rel = fields.Selection(related='lead_id.dip_type', string='Category', readonly=True, store=True)
	project_status_id_rel = fields.Many2one(related='lead_id.project_status_id', string='Project Status', readonly=True, store=True)
	project_lifespan_rel = fields.Char(related='lead_id.project_lifespan', string='Project Lifespan', readonly=True, store=True)
	estimated_closing_date_rel = fields.Date(related='lead_id.estimated_closing_date', string='Estimated Closing Date', readonly=True, store=True)
	engagement_date_rel = fields.Date(related='lead_id.engagement_date', string='Engagement Date', readonly=True, store=True)
	customer_zip_rel = fields.Char(related='lead_id.partner_id.zip', string='Postal Code', readonly=True, store=True)
	customer_state_id_rel = fields.Many2one(related='lead_id.partner_id.state_id', string='State', readonly=True, store=True)

	#groups field
	is_group_iconnexion_design_owner_manager = fields.Boolean(string='Design Owner Manager', compute='_compute_is_in_group')

	@api.constrains('no_of_per')
	def _restriction_no_of_per(self):
		for part in self:
			if (part.lead_id.is_mccoy or part.lead_id.is_iconnexion) and part.no_of_per < 1:
				raise ValidationError('No of Per cannot be %s.' % part.no_of_per)

	def _compute_quote_unit_price(self):
		for part in self:
			part.quoted_price_2 = part.quoted_price		
			order_id =  self.env['sale.order'].search([('opportunity_id','=',part.lead_id.id)],limit=1)
			if order_id and part.product_id:
				line_ids =  self.env['sale.order.line'].search([('product_id','=',part.product_id.id),('order_id','=',order_id.id)],limit=1)
				if line_ids:
					part.quoted_price_2 = line_ids.quote_price_unit
						

	@api.depends('remarks_ids.date', 'remarks_ids.remarks', 'lead_id.odes_stage_ids.backward_reason')
	def _compute_last_remark(self):
		for part in self:
			date = ''
			remarks = ''
			reason = ''
			last_stage = ''
			for remark in part.remarks_ids:
				date = remark.date
				info = remark.remarks
				remarks = info
			if part.lead_id:
				last_stage = part.lead_id and part.lead_id.odes_stage_ids and part.lead_id.odes_stage_ids.sorted(key=lambda s: s.create_date)[-1] or False

			part.last_remark_date = date
			part.last_remark = remarks
			part.last_reason = last_stage.backward_reason if last_stage else False

	@api.model_create_multi
	def create(self, vals_list):
		crm_lead_obj = self.env['crm.lead']
		for vals in vals_list:
			lead_id = vals.get('lead_id')
			if lead_id:
				lead = crm_lead_obj.browse(lead_id)
				if lead.design_owner_id:
					vals['design_owner_id'] = lead.design_owner_id.id
		return super(OdesPart, self).create(vals_list)

	#group function
	def _compute_is_in_group(self):
		for leads in self:
			if self.user_has_groups('iconnexion_mccoy_custom.group_iconnexion_design_owner_manager'):
				leads.is_group_iconnexion_design_owner_manager = True
			else:
				leads.is_group_iconnexion_design_owner_manager = False

	@api.constrains('design_owner_id')
	def update_related_design_owner_ids(self):
		crm_lead_obj = self.env['crm.lead']
		odes_part_obj = self.env['odes.part']
		for part in self:
			leads = crm_lead_obj.search([('id', '=', part.lead_id.id)])
			for lead in leads:
				if lead.design_owner_id.id != part.design_owner_id.id:
					lead.write({'design_owner_id': part.design_owner_id.id})
					odes_parts = odes_part_obj.search([('lead_id', '=', lead.id)])
					odes_parts.write({'design_owner_id': part.design_owner_id.id})

	def action_change_crm_stage(self):
		return {
			'name': ('Change Stage'),
			'type':'ir.actions.act_window', 
			'view_type':'form', 
			'view_mode':'form',
			'res_model':'odes.crm.backward.stage.wizard', 
			'target': 'new',
			'context': self.env.context
		}

class SampleRequest(models.Model):
	_inherit = "sample.request.form"

	@api.onchange('partner_id')
	def _onchange_partner_id(self):
		for req in self:
			stock_location = self.env['stock.location'].search([('is_sample_location','=',True),('usage','=','internal'),('company_id','=',self.env.company.id)])
			if stock_location:
				return {'domain': {'location_id': [('is_sample_location','=', True)]}}
			else:
				return

	@api.model
	def default_get(self, fields):
		res = super(SampleRequest, self).default_get(fields)
		active_ids = self.env.context.get('active_ids', [])
		picking_obj = self.env['stock.picking']
		list_name = ""
		location_id = False
		location_ids = self.env['stock.location'].search([('is_sample_location','=',True),('usage','=','internal'),('company_id','=',self.env.company.id)])
		if location_ids:
			location_id = location_ids.id
		no = 1
		active_ids = self.env.context.get('active_ids', [])
		picking_obj = self.env['stock.picking']
		list_name = ""
		list_data = []
		no = 1

		lead_obj = self.env['crm.lead']
		for leads in lead_obj.browse(active_ids):
			for pline in leads.odes_part_ids:
				if pline.product_id:
					list_data.append([0, 0, {
						'product_id': pline.product_id.id,
						'qty': 0,
					}])
		res['location_id'] = location_id
		res['product_line'] = list_data
		return res

	def button_approve(self):
		active_ids = self.env.context.get('active_ids', [])
		for rec in self:
			
			dict_data_po = {}
			
			for line in rec.product_line:
				if line.product_id.id not in dict_data_po:
					list_data_po = []
					list_data_po.append(line)
					data_po = {'lines': list_data_po}
					
					dict_data_po[line.product_id.id] = data_po
				else:
					list_data_po.append(line)
					dict_data_po[line.product_id.id]['lines'] = list_data_po
			stock_data_list = []
			po_vals = []
			list_order_line = []
			for data in dict_data_po:
				po_vals = rec.sudo()._prepare_auto_receipt_data(data)
				item_list_ids = []				
				for line_data in dict_data_po[data]['lines']:
					if line_data.qty > 0:
						# po_vals['order_line'] += [(0, 0, rec._prepare_auto_purchase_order_line_data(line_data))]
						item_list_ids.append(line_data.product_id.id)
						list_order_line.append((0, 0, rec._prepare_auto_receipt_line_data(line_data)))
			po_vals['move_ids_without_package'] = list_order_line
			stock_picking = self.env['stock.picking'].create(po_vals)	
			
			# try:
			# 	with self.env.cr.savepoint():
			# 		stock_picking._action_done()
			# except (UserError, ValidationError):
			# 	pass
				
			action = self.env.ref('stock.stock_picking_action_picking_type').read()[0]
			action['domain'] = [('id', '=', stock_picking.id)]
			self.state = 'approved'
			self.activity_schedule('iconnexion_custom.mail_activity_data_icon_update_sample_request',user_id=self.env.user.id)
			# return action
			return True
		

	def button_send_item(self):
		active_ids = self.env.context.get('active_ids', [])
		for rec in self:
			dict_data_po = {}
			
			for line in rec.product_line:
				if line.product_id.id not in dict_data_po:
					list_data_po = []
					list_data_po.append(line)
					data_po = {'lines': list_data_po}
					
					dict_data_po[line.product_id.id] = data_po
				else:
					list_data_po.append(line)
					dict_data_po[line.product_id.id]['lines'] = list_data_po
			stock_data_list = []
			po_vals = []
			list_order_line = []
			for data in dict_data_po:
				po_vals = rec.sudo()._prepare_auto_outgoing_data(data)
				item_list_ids = []
				
				for line_data in dict_data_po[data]['lines']:
					if line_data.qty > 0:
						# po_vals['order_line'] += [(0, 0, rec._prepare_auto_purchase_order_line_data(line_data))]
						item_list_ids.append(line_data.product_id.id)
						list_order_line.append((0, 0, rec._prepare_auto_outgoing_line_data(line_data)))
			po_vals['move_ids_without_package'] = list_order_line
			stock_picking = self.env['stock.picking'].create(po_vals)	
			
			# try:
			# 	with self.env.cr.savepoint():
			# 		stock_picking._action_done()
			# except (UserError, ValidationError):
			# 	pass			
				
			self.state = 'done'
			# 	stock_data_list.append(stock_picking.id)
			# self.picking_id =  stock_picking.id
		return True


	def _prepare_auto_receipt_data(self,partner_id):
		
		self.ensure_one()
		
		picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'),('company_id','=',self.company_id.id),('is_sample_request_type','=',True)],limit=1)
		picking_dest_id = self.env['stock.location'].search([('usage', '=', 'internal'),('company_id','=',self.company_id.id)],limit=1)
		vendor_location = self.env['stock.location'].search([('usage', '=', 'supplier'),('company_id','=',self.company_id.id)], limit=1)

		if not picking_type:
			raise ValidationError('Configure the Sample Request Operation Type before proceeding with the process.')
		
		return {
			'origin': self.name,
			'sample_request_id': self.id,
			'partner_id': self.partner_id.id,
			'picking_type_id': picking_type.id,
			'location_dest_id': self.location_id.id,
			'location_id': vendor_location.id,
			'scheduled_date': self.project_start_date,
			'move_ids_without_package': [],
		}

	def _prepare_auto_outgoing_data(self,partner_id):
		
		self.ensure_one()
		picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),('company_id','=',self.company_id.id),('is_sample_request_type','=',True)],limit=1)
		picking_dest_id = self.env['stock.location'].search([('usage', '=', 'internal'),('company_id','=',self.company_id.id)],limit=1)
		customer_location = self.env['stock.location'].search([('usage', '=', 'customer')], limit=1)

		if not picking_type:
			raise ValidationError('Configure the Sample Request Operation Type before proceeding with the process.')
		return {
			'origin': self.name,
			'sample_request_out_id': self.id,
			'partner_id': self.partner_id.id,
			'picking_type_id': picking_type.id,
			'location_dest_id': customer_location.id,
			'location_id': self.location_id.id,
			'scheduled_date': self.project_start_date,
			'move_ids_without_package': [],
		}
