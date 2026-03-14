# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse


class Users(models.Model):
	_inherit = "res.users"
	
	report_user_id = fields.Many2one('res.users', 'Report to')
	report_user_ids = fields.One2many('res.users', 'report_user_id', string="Report by")
	report_to_user_ids = fields.Many2many('res.users','res_users_email_rel','user_id','user_id2', string="Report By")
	report_to_user_crm_ids = fields.Many2many('res.users','res_users_crm_rel','user_id','user_id2', string="Report By (CRM)")
	report_to_user_contact_ids = fields.Many2many('res.users','res_users_contact_rel','user_id','user_id2', string="Report By (Contact)")
	is_select_company = fields.Boolean('Select Company')
	#alter table res_users add column report_user_id integer;
	#alter table res_users add column is_select_company boolean;

	@api.onchange('is_select_company')
	def is_select_company_change(self):
		vals = {} 
		if self.is_select_company == True:
			vals['action_id'] =  self.env.ref('iconnexion_custom.action_icon_select_company_wizard').id

		if self.is_select_company == False:
			vals['action_id'] = False
		self.update(vals)

class IrModelData(models.Model):
		_inherit = "ir.model.data"

		def init(self):
			menu_obj = self.env["ir.model.data"]
			menus = menu_obj.search([('name', '=', 'email_template_edi_sale'),('module', '=', 'sale')])
			# dd
			menus.write({'noupdate' : False})