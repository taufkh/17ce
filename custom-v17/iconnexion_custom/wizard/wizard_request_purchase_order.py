from odoo import api, fields, models, tools, _
from dateutil.relativedelta import relativedelta

class IconRequestPurchaseOrderWizard(models.TransientModel):
	_name = "icon.request.purchase.order.wizard"
	_description = "Icon Request Purchase Order Wizard"

	name = fields.Char(string="Name")
	date_start = fields.Date('Starting Date', default=fields.Date.today())
	line_ids = fields.One2many('icon.request.purchase.order.wizard.line', 'request_id', string="Lines")



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
					qty_demand = dict_data_po[line]['product_qty']
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
						'qty': qty_demand + minimum_stock,
						'qty_demand': qty_demand,
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

	def action_create_po(self):
		active_ids = self.env.context.get('active_ids', [])
		for rec in self:
			
			dict_data_po = {}
			
			# list_data_po = []
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
			# print (dict_data_po, 'dict_data_po')
			for data in dict_data_po:
				po_vals = rec.sudo()._prepare_auto_purchase_order_data(data)
				item_list_ids = []
				list_order_line = []
				for line_data in dict_data_po[data]['lines']:
					if line_data.qty > 0:
						# po_vals['order_line'] += [(0, 0, rec._prepare_auto_purchase_order_line_data(line_data))]
						item_list_ids.append(line_data.product_id.id)
						list_order_line.append((0, 0, rec._prepare_auto_purchase_order_line_data(line_data)))
						# print ('list_order_line',list_order_line)
				po_vals['order_line'] = list_order_line
				
				purchase_order = self.env['purchase.order'].create(po_vals)
				move_ids = self.env['stock.move'].search([('picking_id','in', active_ids),('product_id','in', item_list_ids)])
				# print( move_ids, 'dfdfg')
				if move_ids:
					move_ids.write({'purchase_id' : purchase_order.id})
				sale_ids = self.env['sale.order.line'].search([('order_id','in', active_ids),('product_id','in', item_list_ids)])
				if sale_ids:
					sale_ids.write({'icon_purchase_id': purchase_order.id})
					# icon_purchase_line_id#how to get pruchase line _id ,
					# dari setiap po line terhubung ke sale line
					# dar ipurchase_line masukin many2 many
				purchase_data_list.append(purchase_order.id)
				for pol in purchase_order.order_line:
					if pol.icon_move_id:
						pol.icon_move_id.write({'created_purchase_line_id':pol.id})
					# print ('adfadfasdfasdfadfadfasdf')
					# print (pol.icon_move_id)


			action = self.env.ref('purchase.purchase_form_action').read()[0]
			
			action['domain'] = [('id', '=', purchase_data_list)]
			return action
				# for line in rec.line_ids:
				#     if line.qty > 0:
				#         line.move_id.write({'purchase_id' : purchase_order.id})
			# gg


	def _prepare_auto_purchase_order_data(self,partner_id):
		
		self.ensure_one()
		list_so = []
		payment_term_id = False
		freight_terms = ''
		for data in self.line_ids:
			list_so.append(data.icon_sale_id.id)
		picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'),('company_id','=',self.env.user.company_id.id)],limit=1)
		term = self.env['res.partner'].browse(partner_id)
		if term.property_payment_term_id:
			payment_term_id = term.property_payment_term_id.id
		freight_terms = term.freight_terms
		return {
			'name': self.env['ir.sequence'].sudo().next_by_code('purchase.order'),
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
			'product_qty': line.qty,
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
	_name = "icon.request.purchase.order.wizard.line"
	_description = "Icon Request Purchase Order Wizard Line"

	request_id = fields.Many2one('icon.request.purchase.order.wizard', string="Request id")
	product_id = fields.Many2one('product.product', string="Product")
	name = fields.Char('CPN')
	move_id = fields.Many2one('stock.move', string="Move")
	partner_id = fields.Many2one('res.partner', string='Vendor', help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
	
	qty = fields.Float(string="Quantity")
	qty_demand = fields.Float(string="Quantity Demand")
	picking_id = fields.Many2one('stock.picking', string="From Picking Out")
	icon_sale_id = fields.Many2one('sale.order', string="SO Number")
	icon_sale_line_id = fields.Many2one('sale.order.line', string="SO Number Line")
	stock_move_id = fields.Many2one('stock.move', string="Stock Move") #modified 27 05 2022
	is_create_po = fields.Boolean(string="Create PO")
	icpo_request_deliver_date = fields.Date('ICPO Request Delivery Date') #ICPO request delivery date. 1 week before Customer req date
	customer_id = fields.Many2one('res.partner', string='Customer')
	price = fields.Float(string='Price')


