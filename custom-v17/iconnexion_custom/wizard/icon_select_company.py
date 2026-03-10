from datetime import datetime, timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast


class IconSelectCompanyWizard(models.TransientModel):
	_name = "icon.select.company.wizard"
	_description = "Select Company Wizard"

	company_id = fields.Many2one('res.company', string='Company')
	companys = fields.Selection([
        ('McCoy Pte Ltd', 'McCoy Pte Ltd'),
        ('ODES', 'ODES'),        
        ('iConnexion Asia Pte Ltd', 'iConnexion Asia Pte Ltd')      
    ], string='Target Company')#using selection due other user canot see company

	def button_change(self):
		company_ids = self.env['res.company'].sudo().search([('name','=',self.companys)],limit=1)
		if company_ids:
			self.env.user.sudo().write({'company_id': company_ids.id,'company_ids': [(6,0,[company_ids.id])]})
			if company_ids.name == 'iConnexion Asia Pte Ltd':
				self.env.user.sudo().write({'in_group_132': True,'company_ids': [(6,0,[company_ids.id])]})
		 # self.env.user.write({'company_ids': [(6,0,self.company_id.id)]}) 'company_ids': [(6,0,self.company_id.id)]
		 # [(6, 0, lines1)],
		# return {
		# 	 'type': 'ir.actions.client',
		# 	 'tag': 'reload',
		# }

		# action_id =  self.env.ref('iconnexion_custom.action_icon_select_company_wizard').id
		# print ('teatetateat',action_id)944
		return {
	      'type': 'ir.actions.act_url',
	      'target': 'self',
	      'url': 'web#cids=1&home='
	   }

# action_id = fields.Many2one('ir.actions.actions', string='Home Action',
        # help="If specified, this action will be opened at log on for this user, in addition to the standard menu.")

# class IconSalePopupWizard(models.TransientModel):
# 	_name = "icon.sale.popup.wizard"

# 	name = fields.Char('Reason')
