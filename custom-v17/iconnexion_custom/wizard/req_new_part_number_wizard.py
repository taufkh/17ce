from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ReqNewPartNumberWizard(models.Model):
	# _inherit = "crm.lead"

	_name = "req.new.part.number.wizard"
	_description = "Request New Part Number Wizard"


	id_number = fields.Char(string="ID Number", required=True, copy=False, readonly=True, default=lambda self: _('New'))
	desc =fields.Char("Description", required=True)
	name = fields.Char("MPN", required=True)
	state = fields.Selection([('request', 'Request'),('inprocess', 'In Process'),('decline', 'Decline'),('created', 'Created')], string="Status", default="request")
	brand_id = fields.Many2one("product.brand", string="Brand", required=True)
	product_type = fields.Selection([('consu','Consumable'),('service','Service'),('product','Storable Product')],string="Type 2",default="product", required=False)
	icon_type_id = fields.Many2one("iconnexion.product.type",string="Type", required=True)
	class_id = fields.Many2one("product.class", string="Class", required=True)
	category_id = fields.Many2one("product.category", string="Category", required=True)
	uom_id = fields.Many2one("uom.uom", string="UOM", required=True)
	req_new_part_number_id = fields.Many2one ("crm.lead", "CRM Leaed")
	company_id = fields.Many2one('res.company',string='Company',default=lambda self: self.env.company.id)
	
	# 1. buat kan halaman list
	# 2. ganti nama
	# 3. pindahkan ke purchase
	# 4. buat tombol lalu create ke product.product
	# tombol
	# create product.product

	def button_confirm(self):
		partner_ids = []
		self.req_new_part_number_id.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
								'iconnexion_custom.new_part_number_approve',
							values={'part_number': self,},
							subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
							partner_ids=partner_ids,
							subject='Part Number Request '+ self.name,                            
					) 
		
		self.state = 'inprocess'

	def button_reject(self):
		partner_ids = []
		self.req_new_part_number_id.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
								'iconnexion_custom.new_part_number_rejected',
							values={'part_number': self,},
							subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
							partner_ids=partner_ids,
							subject='Part Number Request '+ self.name,                            
					) 
		self.state = 'decline'
		
	def button_create(self):
		partner_ids = []
		self.req_new_part_number_id.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
								'iconnexion_custom.new_part_number_created',
							values={'part_number': self,},
							subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
							partner_ids=partner_ids,
							subject='Part Number Request '+ self.name,                            
					) 
		vals= {
			'name' : self.name,
			# 'default_code' : self.id_number,
			'description_mpn' : self.desc,
			'product_brand_id' : self.brand_id.id,
			'type': self.product_type,
			'icon_type_id' : self.icon_type_id.id,
			'class_id' : self.class_id.id,
			'categ_id' : self.category_id.id,
			'uom_id' : self.uom_id.id,
			'uom_po_id' : self.uom_id.id,
			'company_id': self.company_id.id,
		}
		# 
		product_ids = self.env['product.template'].search([('name','=',self.name)])
		for product in product_ids:
			raise ValidationError("This Item Already in System, Please Check Your MPN Request")

		
		self.env['product.template'].create(vals)
		self.state = 'created'

		@api.model_create_multi
		def create(self, vals_list):
			for vals in vals_list:
				if vals.get('id_number', _('New')) == _('New'):
					vals['id_number'] = self.env['ir.sequence'].next_by_code('req.new.part.number.wizard') or _('New')
			return super(ReqNewPartNumberWizard, self).create(vals_list)
		

		
