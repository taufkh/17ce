from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class IconRequestPurchaseOrderWizard(models.TransientModel):
	_inherit = "icon.request.purchase.order.wizard"
	_description = "Icon Request Purchase Order Wizard"


	@api.model
	def default_get(self, fields):
		res = super(IconRequestPurchaseOrderWizard, self).default_get(fields)
		active_ids = self.env.context.get('active_ids', [])
		picking_obj = self.env['stock.picking']
		list_name = ""
		list_data = []
		no = 1
		sale_obj = self.env['sale.order']
		sale_line_obj = self.env['sale.order.line']
		for sale_orders in sale_obj.browse(active_ids):
			for delivery in sale_orders.picking_ids:
				if no != len(active_ids):
					list_name += delivery.origin or "" + ","
				else:
					list_name += delivery.origin or ""
				no += 1

				dict_data_po = {}
				total_qty_sum = 0
				not_combine = True
				# list_data_po = []
				for line in delivery.move_ids_without_package:
					icpo_request_deliver_date = ''
					
					if not line.purchase_id:
						# if line.product_id.id not in dict_data_po:
						if not_combine:
							sale_line_id = False
							if line.sale_line_id:                                
								icpo_request_deliver_date = line.sale_line_id.icpo_request_deliver_date
								sale_line_id = line.sale_line_id.id
								
							data_po = {'product_qty': line.product_uom_qty,'picking_id':delivery.id,
							'icon_sale_id':sale_orders.id,'icon_sale_line_id':sale_line_id,
							'icpo_request_deliver_date':icpo_request_deliver_date,'stock_move_id': line.id,
							'name': line.name,'product_id':line.product_id.id} #modified 27 05 2022
							# dict_data_po[line.product_id.id] = data_po
							dict_data_po[line.id] = data_po
						# else:
						# 	total_qty_sum = dict_data_po[line.product_id.id]['product_qty'] + line.product_uom_qty
						# 	dict_data_po[line.product_id.id]['product_qty'] = total_qty_sum
				# print (dict_data_po, 'ffg')

				for line in dict_data_po:
					# print (line, 'dffg')
					qty = dict_data_po[line]['product_qty']
					picking_id = dict_data_po[line]['picking_id']
					icon_sale_id = dict_data_po[line]['icon_sale_id']
					name = dict_data_po[line]['name']
					icon_sale_line_id = dict_data_po[line]['icon_sale_line_id']
					icpo_request_deliver_date = dict_data_po[line]['icpo_request_deliver_date']
					stock_move_id = dict_data_po[line]['stock_move_id'] #modified 27 05 2022
					product = self.env['product.product'].browse(dict_data_po[line]['product_id'])
					# product = self.env['product.product'].browse(line)

					""" TODO BROWSE THIS ID TOMMOROW AND GET THE IS_SPECIAL_PRICE """
					sale_line = sale_line_obj.sudo().browse(icon_sale_line_id) #added 11 07 2022(added special price, delvin)
					is_special_price = sale_line.is_special_price

					minimum_stock = 0
					
					if product.orderpoint_ids:
						for orderpoint in product.orderpoint_ids:
							minimum_stock = orderpoint.product_min_qty

					if is_special_price:
						for vendors in product.seller_ids:
							if vendors.customer_id.id == sale_line.order_id.partner_id.id:
								vendor = vendors.name.id
								price = vendors.price
								break
					else:
						vendor = product.product_tmpl_id.manufacturing_company_id.id
						price = product.standard_price

					list_data.append([0, 0, {
						'product_id': product.id,
						'name': name,
						'partner_id': vendor or False,
						'qty': qty,
						'picking_id': picking_id,
						'icon_sale_id': icon_sale_id,
						'icon_sale_line_id': icon_sale_line_id,
						'icpo_request_deliver_date': icpo_request_deliver_date,
						'stock_move_id': stock_move_id, #modified 27 05 2022
						'price': price,
						# 'move_id' : line.id
						 
					}])
			
		res['line_ids'] = list_data
		res['name'] = list_name
		
		return res

	# def action_link_buffer_stock(self):
	# 	for rec in self:
	# 		for line in rec.line_ids:
				
	def action_link_buffer_stock(self):
		active_ids = self.env.context.get('active_ids', [])
		for i in self:
			for line in i.line_ids:
				if line.receipt_line_ids:
					line.create_buffer_stock_lines()
					sale_lines = self.env['sale.order.line'].search([
						('product_id', '=', line.product_id.id),
						('order_id', 'in', active_ids),
					])
					sale_lines.write({'icon_purchase_ids': [(4, line.id) for line in line.receipt_line_ids.move_id.purchase_line_id]})

			if not any(line.receipt_line_ids for line in i.line_ids):
				raise UserError(_("Cannot link to buffer stock."))

		for line in self.line_ids:
			line.receipt_line_ids = False

		return {
			'name': 'Create PO (iConnexion)',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'icon.request.purchase.order.wizard',
			'res_id': self.id,
			'target': 'new',
			'context': {'default_line_ids': [(6, 0, self.line_ids.ids)], 'default_receipt_line_ids': False},
		}
			


	def action_create_po(self):
		active_ids = self.env.context.get('active_ids', [])
		for rec in self:
			dict_data_po = {}
			for line in rec.line_ids:
				if line.partner_id.id not in dict_data_po:
					list_data_po = []
					list_data_po.append(line)
					data_po = {'lines': list_data_po}
					dict_data_po[line.partner_id.id] = data_po
				else:
					list_data_po.append(line)
					dict_data_po[line.partner_id.id]['lines'] = list_data_po
			purchase_data_list = []
			for data in dict_data_po:
				po_vals = rec.sudo()._prepare_auto_purchase_order_data(data)
				item_list_ids = []
				list_order_line = []
				for line_data in dict_data_po[data]['lines']:
					print(line_data.qty_demand)
					if line_data.qty > 0:
						item_list_ids.append(line_data.product_id.id)
						list_order_line.append((0, 0, rec._prepare_auto_purchase_order_line_data(line_data)))
					if line_data.qty_demand <= 0:
						raise UserError(_("Please remove the item with a quantity demand of %s before creating a purchase order.") % line_data.qty_demand)
				po_vals['order_line'] = list_order_line
				purchase_order = self.env['purchase.order'].create(po_vals)
				purchase_order.write({
					'name': self.env['ir.sequence'].sudo().next_by_code('purchase.order'),
				})
				move_ids = self.env['stock.move'].search([('picking_id','in', active_ids),('product_id','in', item_list_ids)])
				if move_ids:
					move_ids.write({'purchase_id' : purchase_order.id})
				sale_ids = self.env['sale.order.line'].search([('order_id','in', active_ids),('product_id','in', item_list_ids)])
				if sale_ids:
					sale_ids.write({'icon_purchase_id': purchase_order.id})
				purchase_data_list.append(purchase_order.id)
				for pol in purchase_order.order_line:
					if pol.icon_move_id:
						pol.icon_move_id.write({'created_purchase_line_id':pol.id})
				# move the following code block outside the pol loop
				count = -1
				line_order_ids = [pol.id for pol in purchase_order.order_line]
				for lines in rec.line_ids:
					count += 1
					if lines.receipt_line_ids:
						raise UserError(_("Please remove the receipt first before creating a purchase order."))
					if lines.qty_demand <= 0:
						raise UserError(_("Please remove the item with a quantity demand of %s before creating a purchase order.") % lines.qty_demand)
					lines.create_buffer_stock(list_order_line_id=line_order_ids[count])
			action = self.env.ref('purchase.purchase_form_action').read()[0]
			action['domain'] = [('id', '=', purchase_data_list)]
			return action


	def _prepare_auto_purchase_order_data(self,partner_id):
		
		self.ensure_one()
		list_so = []
		payment_term_id = False
		freight_terms = ''
		for data in self.line_ids:
			list_so.append(data.icon_sale_id.id)
		picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'),('company_id','=',self.env.company.id)],limit=1)
		term = self.env['res.partner'].browse(partner_id)
		if term.property_payment_term_id:
			payment_term_id = term.property_payment_term_id.id
		freight_terms = term.freight_terms
		return {
			'name': 'Draft',
			'origin': self.name,
			'icon_related_so_ids': list_so,
			'partner_id': partner_id,
			'picking_type_id': picking_type.id,
			'date_order': fields.datetime.now(),
			# 'company_id': company.id,
			# 'fiscal_position_id': company_partner.property_account_position_id.id,
			'payment_term_id': payment_term_id,#company_partner.property_supplier_payment_term_id.id,
			'freight_terms': freight_terms,
			# 'auto_generated': True,
			# 'auto_sale_order_id': self.id,
			# 'partner_ref': self.name,
			'currency_id': self.env.user.company_id.currency_id.id,
			'order_line': [],
		}

	@api.model
	def _prepare_auto_purchase_order_line_data(self, line):
		
		return {
			'name': line.name,
			'product_qty': line.qty_demand,
			'product_id': line.product_id and line.product_id.id or False,
			'product_uom': line.product_id and line.product_id.uom_po_id.id or line.product_uom.id,
			'price_unit': line.price,
			'icon_picking_ref_id': line.picking_id.id,
			'icon_sale_id': line.icon_sale_id.id,
			'icon_sale_ids': [(6, 0, [line.icon_sale_line_id.id])],
			'icpo_request_deliver_date': line.icpo_request_deliver_date,
			'icon_move_id': line.stock_move_id.id, #modified 27 05 2022
			# 'company_id': company.id,
			# 'date_planned': so_line.order_id.expected_date or date_order,
			# 'taxes_id': [(6, 0, company_taxes.ids)],
			# 'display_type': so_line.display_type,
		}

class IconRequestPurchaseOrderWizardLine(models.TransientModel):
	_inherit = "icon.request.purchase.order.wizard.line"


	qty_demand = fields.Float(string="Quantity Demand", compute="_compute_quantities")
	so_qty = fields.Float(string="SO Quantity", compute="_compute_quantities")
	linked_qty = fields.Float(string="Linked Quantity", compute="_compute_quantities")
	linked_purchase_order_lines = fields.Many2many(
    'purchase.order.line',
    string='Linked Purchase Order Lines',
    related='icon_sale_line_id.icon_purchase_ids',
    readonly=True)
	buffer_stocks = fields.Float(string='Buffer Stocks', compute="_compute_buffer_stock")
	available_stock = fields.Float(string='Available Stock', compute="_compute_available_stock")
	receipt_line_ids = fields.Many2many('stock.move.line', string='Receiving')

	def _compute_available_stock(self):
		for line in self:
			stock = 0.0
			if line.product_id:
				quant_objs = self.env['stock.quant'].search([('product_id', '=', line.product_id.id)])
				if quant_objs:
					stock = sum(quant_obj.available_quantity for quant_obj in quant_objs if quant_obj.location_id.usage == 'internal')
			line.available_stock = stock

	def _compute_quantities(self):
		for line in self:
			# Compute SO Quantity
			line.so_qty = line.icon_sale_line_id.product_uom_qty

			# Compute Linked Quantity
			buffer_stock_lines = self.env['buffer.stock.line'].search([('sale_order_line_id', '=', line.icon_sale_line_id.id)])
			line.linked_qty = sum(buffer_stock_lines.mapped('stock_used'))

			# Compute Quantity Demand
			line.qty_demand = line.so_qty - line.linked_qty

		
	def create_buffer_stock_lines(self):
		for i in self:
			receipt_lines = i.receipt_line_ids.sorted(key=lambda r: r.write_date)
			remaining_qty = i.qty
			buffer_stock = self.env['buffer.stock']
			for line in receipt_lines:
				if line:
					if remaining_qty <= 0 or line.buffer_stocks <= 0:
						raise ValidationError("Please check the Buffer Stock or input Quantity")
					if i.qty_demand < i.qty:
						raise ValidationError("Please check the Quantity Demand or input Quantity")
					existing_line = self.env['buffer.stock'].search([
						('product_id', '=', line.product_id.id),
						('quantity', '>', 0), ('stock_move_line_id', '=', line.id)
					])
					if existing_line:
						qty_to_update = min(existing_line.quantity, remaining_qty)
						qty_diff = existing_line.quantity - remaining_qty
						remaining_qty -= qty_to_update
						existing_line.quantity -= qty_to_update
						existing_line.stock_used += qty_to_update
						buffer_stock |= existing_line
						# existing_buffer_line = self.env['buffer.stock'].search([
						# 	('product_id', '=', line.product_id.id),
						# 	('quantity', '>', 0), ('buffer_stock_id', '=', existing_line.id)
						# ])
						self.env['buffer.stock.line'].create({
							'buffer_stock_id': existing_line.id,
							'product_id': line.product_id.id,
							'quantity': qty_diff,
							'stock_used': qty_to_update,
							'sale_order_line_id': i.icon_sale_line_id.id,
							'purchase_order_line_id': line.move_id.purchase_line_id.id,
						})
					elif line.qty_done > 0 and remaining_qty < line.qty_done:
						qty_diff = line.qty_done - remaining_qty
						new_buffer_stock = self.env['buffer.stock'].create({
							'product_id': line.product_id.id,
							'quantity': qty_diff,
							'stock_used': remaining_qty,
							'stock_move_line_id': line.id,
						})
						buffer_stock |= new_buffer_stock
						self.env['buffer.stock.line'].create({
							'buffer_stock_id': new_buffer_stock.id,
							'product_id': line.product_id.id,
							'quantity': qty_diff,
							'stock_used': remaining_qty,
							'sale_order_line_id': i.icon_sale_line_id.id,
							'purchase_order_line_id': line.move_id.purchase_line_id.id,
						})
						remaining_qty = 0
					else:
						qty_used = line.qty_done if remaining_qty >= line.qty_done else remaining_qty
						new_buffer_stock = self.env['buffer.stock'].create({
							'product_id': line.product_id.id,
							'quantity': 0,
							'stock_used': qty_used,
							'stock_move_line_id': line.id,
						})
						buffer_stock |= new_buffer_stock
						self.env['buffer.stock.line'].create({
							'buffer_stock_id': new_buffer_stock.id,
							'product_id': line.product_id.id,
							'quantity': 0,
							'stock_used': qty_used,
							'sale_order_line_id': i.icon_sale_line_id.id,
							'purchase_order_line_id': line.move_id.purchase_line_id.id,
						})
						remaining_qty -= qty_used
			return buffer_stock
		

	def create_buffer_stock(self, list_order_line_id):
		for i in self:
			buffer_stock = self.env['buffer.stock']
			if not i.receipt_line_ids:
				new_buffer_stock = self.env['buffer.stock'].create({
					'product_id': i.product_id.id,
					'quantity': i.qty_demand,
					'stock_used': i.qty_demand,
				})
				buffer_stock |= new_buffer_stock
				buffer_line = self.env['buffer.stock.line'].create({
					'buffer_stock_id': new_buffer_stock.id,
					'product_id': i.product_id.id,
					'quantity': i.qty_demand,
					'stock_used': i.qty_demand,
					'sale_order_line_id': i.icon_sale_line_id.id,
					'purchase_order_line_id': list_order_line_id,
				})


	def _compute_buffer_stock(self):
		for i in self:
			qty_total = 0.0
			move_lines = self.env['stock.move.line'].search([('product_id', '=', i.product_id.id),
																('state', '=', 'done')])
			qty_total += sum(move_lines.mapped('qty_done'))
			moves = self.env['stock.move'].search([('product_id', '=', i.product_id.id)])
			qty_total += sum(moves.mapped('product_uom_qty'))
			i.buffer_stocks = qty_total
