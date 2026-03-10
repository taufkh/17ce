from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class SampleRequest(models.Model):
	_name = "sample.request.form"
	_description = "Sample Request Form"
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'sequence.mixin']

	name = fields.Char(string="ID Number", required=True, copy=False, readonly=True, default=lambda self: _('New'))
	company_id = fields.Many2one('res.company','Distributor')
	user_id = fields.Many2one('res.users', 'Sales Contact')
	contact_id = fields.Many2one("res.partner", "Contact Person")
	partner_id = fields.Many2one("res.partner", "Company")
	crm_id = fields.Many2one('crm.lead','CRM')
	print_name = fields.Char("Print Name")
	aplication = fields.Char("Application")
	project_name = fields.Char("Project Name")
	project_desc = fields.Char("Project Description")
	project_start_date = fields.Date("Project Start Date")
	project_reference_no = fields.Char("Project Reference No.")
	courir = fields.Char("Courir A/C")
	postcode = fields.Char("Postcode",compute='_compute_postcode')
	telephone = fields.Char("Telephone",compute='_compute_telephone')
	email = fields.Char("Email",compute='_compute_email')
	state = fields.Selection([('request', 'Request'),('inprocess', 'In Process'),('decline', 'Decline'),('approved', 'Approved'),('done', 'Done')], string="Status", default="request")
	product_line = fields.One2many('sample.request.line', 'request_id', string="Lines")
	quantity_1 = fields.Float(string="Year 1 (QTY)")
	quantity_2 = fields.Float(string="Year 2 (QTY)")
	prototype_quantity =fields.Float(string="Prototype Quantity")
	production_start_date = fields.Date('Production Start Date')
	date_now = fields.Date('Date', default=fields.Date.today())
	picking_id = fields.Many2one('stock.picking', 'Receipt ID')
	location_id = fields.Many2one('stock.location', 'Location')
	opportunity_id = fields.Many2one('crm.lead', 'Opportunity')
	picking_count = fields.Integer('# Picking', compute='_compute_picking_count')
	picking_out_count = fields.Integer('# Picking Out', compute='_compute_picking_count')
	given_date = fields.Date('Given Date', compute='_compute_given_date')
	received_date = fields.Date('Receive Date', compute='_compute_received_date')

	def _compute_given_date(self):
		for i in self:
			stock_picking = self.env['stock.picking'].search([('sample_request_out_id', '=', self.id), ('state', '=', 'done')], order='id DESC', limit = 1)
			#if stock_picking.date_done:
			i.given_date = stock_picking.date_done


	def _compute_received_date(self):
		for i in self:
			stock_picking = self.env['stock.picking'].search([('sample_request_id', '=', self.id), ('state', '=', 'done')], order='id DESC', limit = 1)
			i.received_date = stock_picking.date_done

	def _compute_picking_count(self):
		for sample in self:
			sample.picking_count = self.env['stock.picking'].search_count(
				[('sample_request_id', '=', self.id)])
			sample.picking_out_count = self.env['stock.picking'].search_count(
				[('sample_request_out_id', '=', self.id)])

	def action_view_picking(self):
		""" This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
		"""
		result = self.env["ir.actions.actions"]._for_xml_id('stock.action_picking_tree_all')
		# override the context to get rid of the default filtering on operation type
		picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'),('company_id','=',self.env.user.company_id.id)],limit=1)
		context = result['context'] = {'default_partner_id': self.partner_id.id, 'default_origin': self.name, 'default_picking_type_id': picking_type.id}
		# pick_ids = self.mapped('picking_ids')
		# # choose the view_mode accordingly
		# if not pick_ids or len(pick_ids) > 1:
		# 	result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
		# elif len(pick_ids) == 1:
		# picking_ids = self.env['stock.picking'].search([('sample_request_id', '=', self.id)])
		# if not picking_ids or len(picking_ids) > 1:
		# 	result['domain'] = "[('id','in',%s)]" % (picking_ids)
		# elif len(pick_ids) == 1:
		# 	res = self.env.ref('stock.view_picking_form', False)
		# 	form_view = [(res and res.id or False, 'form')]
		# 	if 'views' in result:
		# 		result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
		# 	else:
		# 		result['views'] = form_view
			
		# 	result['res_id'] = picking_ids.id
		return {
            'type': 'ir.actions.act_window',
            'name': 'Receipt',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('sample_request_id', '=', self.id)],
            'context': context
        }


		return result

	def action_view_out_picking(self):
		""" This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
		"""
		result = self.env["ir.actions.actions"]._for_xml_id('stock.action_picking_tree_all')
		# override the context to get rid of the default filtering on operation type
		picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),('company_id','=',self.env.user.company_id.id)],limit=1)
		context = result['context'] = {'default_partner_id': self.partner_id.id, 'default_origin': self.name, 'default_picking_type_id': picking_type.id}
	
		return {
            'type': 'ir.actions.act_window',
            'name': 'Outgoing',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('sample_request_out_id', '=', self.id)],
            'context': context
        }


		return result

	@api.model
	def default_get(self, fields):
		res = super(SampleRequest, self).default_get(fields)
		active_ids = self.env.context.get('active_ids', [])
		picking_obj = self.env['stock.picking']
		list_name = ""
		location_id = False
		location_ids = self.env['stock.location'].search([('name','like','sample'),('usage','=','internal'),('company_id','=',self.env.company.id)])
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

	def button_confirm(self):
		for product in self.product_line:
			if product.qty <= 0:
				raise ValidationError("Please make sure all product have quantity before proceeding !")
		self.state = 'inprocess'
		for sample in self:
			if sample.name:
				partner_ids = []
				if sample.product_line.product_id.product_brand_id:
					for partner_id in sample.product_line.product_id.product_brand_id.icon_product_partner_manager_ids:
						partner_ids.append(partner_id.id)
				# for cs in self.company_id.icon_product_manager_ids:
				# 	partner_ids.append(cs.id)
				if partner_ids:
					 sample.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
							'iconnexion_custom.sampe_request_confirm_template',
						values={'sample': sample,},
						subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
						partner_ids=partner_ids,
						subject='Sample Requested on '+ sample.name,                            
				)


	def button_reject(self):
		self.state = 'decline'

	def button_sample_crm(self):
		context = dict(self.env.context or {})
		list_product_line = []
		for product in self:
			if len(product.product_line) > 1:
				raise ValidationError("You have product in Sample Request Before, please remove it")

			
			if product.opportunity_id:
				for part in product.opportunity_id.odes_part_ids:
					if part.product_id:
						# moqs = part.product_id.product_tmpl_id.moq_ids.filtered(lambda line: (line.product_variant_id==part.product_id or not line.product_variant_id) )
						# moqzz_id = False
						# r_code = 0
						# moq = 0
						# spq = part.product_id.product_tmpl_id.qty_multiply
						# if moqs:
						#     moq = moqs[0].min_qty
						#     r_code = moqs[0].r_code
						#     moq_id = moqs[0].id
						list_product_line.append((0, 0, {'product_id':part.product_id.id}))
			product.write({'product_line':list_product_line })
		return True

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
			
			try:
				with self.env.cr.savepoint():
					stock_picking._action_done()
			except (UserError, ValidationError):
				pass
				
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
			
			try:
				with self.env.cr.savepoint():
					stock_picking._action_done()
			except (UserError, ValidationError):
				pass			
				
			self.state = 'done'
			# 	stock_data_list.append(stock_picking.id)
			# self.picking_id =  stock_picking.id
		return True

	def _prepare_auto_receipt_data(self,partner_id):
		
		self.ensure_one()
		
		picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'),('company_id','=',self.company_id.id)],limit=1)
		picking_dest_id = self.env['stock.location'].search([('usage', '=', 'internal'),('company_id','=',self.company_id.id)],limit=1)
		vendor_location = self.env['stock.location'].search([('usage', '=', 'supplier'),('company_id','=',self.company_id.id)], limit=1)
		
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

	@api.model
	def _prepare_auto_receipt_line_data(self, line):
		
		return {
			'name': line.product_id.name,
			'qty_ctn': line.qty,
			'product_id': line.product_id and line.product_id.id or False,
			'product_uom': line.product_id and line.product_id.uom_po_id.id or line.product_uom.id,
			'product_uom_qty': line.qty,
			'price_unit': line.product_id.standard_price,
		}

	def _prepare_auto_outgoing_data(self,partner_id):
		
		self.ensure_one()
		picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),('company_id','=',self.company_id.id)],limit=1)
		picking_dest_id = self.env['stock.location'].search([('usage', '=', 'internal'),('company_id','=',self.company_id.id)],limit=1)
		customer_location = self.env['stock.location'].search([('usage', '=', 'customer')], limit=1)
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

	@api.model
	def _prepare_auto_outgoing_line_data(self, line):
		
		return {
			'name': line.product_id.name,
			'qty_ctn': line.qty,
			'product_id': line.product_id and line.product_id.id or False,
			'product_uom': line.product_id and line.product_id.uom_po_id.id or line.product_uom.id,
			'product_uom_qty': line.qty,
			'price_unit': line.product_id.standard_price,
		}

	def _compute_postcode(self):
		for i in self:
			if i.contact_id:
				i.postcode = i.contact_id.zip
			else:
				i.postcode = False
			
	def _compute_email(self):
		for i in self:
			if i.contact_id:
				i.email = i.contact_id.email
			else:
				i.email = False

	def _compute_telephone(self):
		for i in self:
			if i.contact_id:
				i.telephone = i.contact_id.phone
			else:
				i.telephone = False

	@api.model_create_multi
	def create(self, vals_list):
		for vals in vals_list:
			if vals.get('name', _('New')) == _('New'):
				vals['name'] = self.env['ir.sequence'].next_by_code('sample.request.form') or _('New')
		return super(SampleRequest, self).create(vals_list)


class SampleRequestLine(models.Model):
	_name = "sample.request.line"
	_description = "Icon Request Purchase Order Wizard Line"

	request_id = fields.Many2one('sample.request.form', string="Request id")
	product_id = fields.Many2one('product.product', string="Product")
	qty = fields.Float(string="Quantity")
	delivery_date = fields.Date('Delivery Date')

	name = fields.Char(string="ID Number", related="request_id.name")
	company_id = fields.Many2one('res.company','Distributor', related="request_id.company_id")
	user_id = fields.Many2one('res.users', 'Sales Contact', related="request_id.user_id")
	contact_id = fields.Many2one("res.partner", "Contact Person", related="request_id.contact_id")
	partner_id = fields.Many2one("res.partner", "Company", related="request_id.partner_id")
	crm_id = fields.Many2one('crm.lead','CRM', related="request_id.crm_id")
	print_name = fields.Char("Print Name", related="request_id.print_name")
	aplication = fields.Char("Application", related="request_id.aplication")
	project_name = fields.Char("Project Name", related="request_id.project_name")
	project_desc = fields.Char("Project Description", related="request_id.project_desc")
	project_start_date = fields.Date("Project Start Date", related="request_id.project_start_date")
	project_reference_no = fields.Char("Project Reference No.", related="request_id.project_reference_no")
	courir = fields.Char("Courir A/C", related="request_id.courir")
	postcode = fields.Char("Postcode", related="request_id.postcode")
	telephone = fields.Char("Telephone",related="request_id.telephone")
	email = fields.Char("Email", related="request_id.email")
	state = fields.Selection(string="Status", related="request_id.state")
	
	quantity_1 = fields.Float(string="Year 1 (QTY)", related="request_id.quantity_1")
	quantity_2 = fields.Float(string="Year 2 (QTY)", related="request_id.quantity_2")
	prototype_quantity =fields.Float(string="Prototype Quantity", related="request_id.prototype_quantity")
	production_start_date = fields.Date('Production Start Date', related="request_id.production_start_date")
	date_now = fields.Date('Date', related="request_id.date_now")
	picking_id = fields.Many2one('stock.picking', 'Receipt ID', related="request_id.picking_id")
	location_id = fields.Many2one('stock.location', 'Location', related="request_id.location_id")
	opportunity_id = fields.Many2one('crm.lead', 'Opportunity', related="request_id.opportunity_id")
	picking_count = fields.Integer('# Picking',  related="request_id.picking_count")
	picking_out_count = fields.Integer('# Picking Out',  related="request_id.picking_out_count")
