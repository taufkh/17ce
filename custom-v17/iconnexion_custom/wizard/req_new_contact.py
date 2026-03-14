from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ReqNewContactWizard(models.Model):
	# _inherit = "crm.lead"

	_name = "req.new.contact.wizard"
	_description = "Request New Contact Wizard"
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'sequence.mixin']

	
	id_number = fields.Char(string="ID Number", required=True, copy=False, readonly=True, default=lambda self: _('New'))
	state = fields.Selection([('request', 'Request'),('inprocess', 'In Process'),('decline', 'Decline'),('created', 'Created')], string="Status", default="request")
	name = fields.Char(string = 'Name', required=True)
	company_type = fields.Selection(string='Company Type', selection=[('person', 'Individual'), ('company', 'Company')], required=True, default='company')
	house_no = fields.Char(string = "House NO")
	level_no = fields.Char(string = "Level No")
	unit_no = fields.Char(string = "Unit NO")
	street = fields.Char(string = "Street")
	street2 = fields.Char(string = "Street 2")
	country_id = fields.Many2one(string="Country", comodel_name='res.country')
	city = fields.Char(string = "City")
	state_id = fields.Many2one(string="state", comodel_name='res.country.state')
	zip_code = fields.Char(string='ZIP')
	uen = fields.Char(string='UEN')
	vat = fields.Char(string='Tax ID')
	peppol_id = fields.Char(string='Peppol ID')
	phone = fields.Char(string='Phone')
	mobile = fields.Char(string='Mobile')
	email = fields.Char(string='Email')
	email_icon = fields.Char(string='Email Iconnexion')	
	website = fields.Char(string='Website Link')	
	category_id = fields.Many2one(string="Tags", comodel_name='res.partner.category')
	customer_code = fields.Char(string="Customer Code")
	user_id = fields.Many2one(string="Salesperson", comodel_name='res.users')
	property_delivery_carrier_id = fields.Many2one(string="Delivery Method", comodel_name='delivery.carrier')
	property_payment_term_id = fields.Many2one(string="Payment Term", comodel_name='account.payment.term')
	freight_terms = fields.Char(string="Freight Terms")
	property_product_pricelist = fields.Many2one(string="Pricelist", comodel_name='product.pricelist')
	bill_to_street = fields.Char('Bill-to Street')
	bill_to_block = fields.Char('Bill-to Block')
	bill_to_city = fields.Char('Bill-to City')
	bill_to_zip = fields.Char('Bill-to Zip')
	bill_to_state = fields.Char('Bill-to State')
	bill_to_country_id = fields.Many2one('res.country',string="Bill-to Country")
	bill_to_street2 = fields.Char('Bill-to Street (2)')
	bill_to_block2 = fields.Char('Bill-to Block (2)')
	bill_to_city2 = fields.Char('Bill-to City (2)')
	bill_to_zip2 = fields.Char('Bill-to Zip (2)')
	bill_to_state2 = fields.Char('Bill-to State (2)')
	bill_to_country2_id = fields.Many2one('res.country',string="Bill-to Country (2)")
	bill_to_street3 = fields.Char('Bill-to Street (3)')
	bill_to_block3 = fields.Char('Bill-to Block (3)')
	bill_to_city3 = fields.Char('Bill-to City (3)')
	bill_to_zip3 = fields.Char('Bill-to Zip (3)')
	bill_to_state3 = fields.Char('Bill-to State (3)')
	bill_to_country3_id = fields.Many2one('res.country',string="Bill-to Country (3)")    
	ship_to_street = fields.Char('Ship-to Street')
	ship_to_block = fields.Char('Ship-to Block')
	ship_to_city = fields.Char('Ship-to City')
	ship_to_zip = fields.Char('Ship-to Zip')
	ship_to_state = fields.Char('Ship-to State')
	ship_to_country_id = fields.Many2one('res.country',string="Ship-to Country")
	ship_to_street2 = fields.Char('Ship-to Street (2)')
	ship_to_block2 = fields.Char('Ship-to Block (2)')
	ship_to_city2 = fields.Char('Ship-to City (2)')
	ship_to_zip2 = fields.Char('Ship-to Zip (2)')
	ship_to_state2 = fields.Char('Ship-to State (2)')
	ship_to_country2_id = fields.Many2one('res.country',string="Ship-to Country (2)")
	ship_to_street3 = fields.Char('Ship-to Street (3)')
	ship_to_block3 = fields.Char('Ship-to Block (3)')
	ship_to_city3 = fields.Char('Ship-to City (3)')
	ship_to_zip3 = fields.Char('Ship-to Zip (3)')
	ship_to_state3 = fields.Char('Ship-to State (3)')
	ship_to_country3_id = fields.Many2one('res.country',string="Ship-to Country (3)")



	def button_confirm(self):
		partner_ids = []
		self.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
								'iconnexion_custom.new_contact_approve',
							values={'contact': self,},
							subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
							partner_ids=partner_ids,
							subject='New Contact Request '+ self.name,                            
					) 
		
		self.state = 'inprocess'

	def button_reject(self):
		partner_ids = []
		self.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
								'iconnexion_custom.new_contact_rejected',
							values={'contact': self,},
							subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
							partner_ids=partner_ids,
							subject='New Contact Request '+ self.name,                            
					) 
		self.state = 'decline'
		
	def button_create(self):
		partner_ids = []
		self.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
								'iconnexion_custom.new_contact_created',
							values={'contact': self,},
							subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
							partner_ids=partner_ids,
							subject='New Contact Request '+ self.name,                            
					) 
		vals= {
			'name' : self.name,
			'company_type' : self.company_type,
			'house_no' : self.house_no,
			'level_no' : self.level_no,
			'unit_no': self.unit_no,
			'street' : self.street,
			'street2' : self.street2,
			'country_id' : self.country_id.id,
			'city' : self.city,
			'state_id' : self.state_id.id,
			'zip': self.zip_code,
			'l10n_sg_unique_entity_number' : self.uen,
			'vat' : self.vat,
			'peppol_id' : self.peppol_id,
			'phone' : self.phone,
			'mobile': self.mobile,
			'email' : self.email,
			'email_icon' : self.email_icon,
			'category_id' : self.category_id.id,
			'website' : self.website,
			'customer_code' : self.customer_code,
			'user_id' : self.user_id.id,
			'property_delivery_carrier_id': self.property_delivery_carrier_id.id,
			'property_payment_term_id': self.property_payment_term_id.id,
			'freight_terms': self.freight_terms,
			'property_product_pricelist': self.property_product_pricelist.id,
			'bill_to_street' : self.bill_to_street,
			'bill_to_block' : self.bill_to_block,
			'bill_to_city': self.bill_to_city,
			'bill_to_zip' : self.bill_to_zip,
			'bill_to_state' : self.bill_to_state,
			'bill_to_country_id' : self.bill_to_country_id.id,
			'bill_to_street2' : self.bill_to_street2,
			'bill_to_block2' : self.bill_to_block2,
			'bill_to_city2': self.bill_to_city2,
			'bill_to_zip2' : self.bill_to_zip2,
			'bill_to_state2' : self.bill_to_state2,
			'bill_to_country2_id' : self.bill_to_country2_id.id,
			'bill_to_street3' : self.bill_to_street3,
			'bill_to_block3' : self.bill_to_block3,
			'bill_to_city3': self.bill_to_city3,
			'bill_to_zip3' : self.bill_to_zip2,
			'bill_to_state3' : self.bill_to_state3,
			'bill_to_country2_id' : self.bill_to_country3_id.id,
			'ship_to_street' : self.ship_to_street,
			'ship_to_block' : self.ship_to_block,
			'ship_to_city': self.ship_to_city,
			'ship_to_zip' : self.ship_to_zip,
			'ship_to_state' : self.ship_to_state,
			'ship_to_country_id' : self.ship_to_country_id.id,
			'ship_to_street2' : self.ship_to_street2,
			'ship_to_block2' : self.ship_to_block2,
			'ship_to_city2': self.ship_to_city2,
			'ship_to_zip2' : self.ship_to_zip2,
			'ship_to_state2' : self.ship_to_state2,
			'ship_to_country2_id' : self.ship_to_country2_id.id,
			'ship_to_street3' : self.ship_to_street3,
			'ship_to_block3' : self.ship_to_block3,
			'ship_to_city3': self.ship_to_city3,
			'ship_to_zip3' : self.ship_to_zip2,
			'ship_to_state3' : self.ship_to_state3,
			'ship_to_country3_id' : self.ship_to_country3_id.id,

		}
		# 
		product_ids = self.env['res.partner'].search([('name','=',self.name)])
		for product in product_ids:
			raise ValidationError("This Contact Already in System, Please Check Your Contact Request")

		
		self.env['res.partner'].create(vals)
		self.state = 'created'

		@api.model_create_multi
		def create(self, vals_list):
			for vals in vals_list:
				if vals.get('id_number', _('New')) == _('New'):
					vals['id_number'] = self.env['ir.sequence'].next_by_code('req.new.contact.wizard') or _('New')
			return super(ReqNewContactWizard, self).create(vals_list)
		
