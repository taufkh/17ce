
from datetime import datetime, timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast


class OdesCrmBackwardStageWizard(models.TransientModel):
	_inherit = "odes.crm.backward.stage.wizard"

	def _get_lead_id(self):
		context = dict(self._context or {})
		active_model = context.get('active_model')
		active_id = context.get('active_id')

		if not active_model or not active_id:
			return

		if active_model == 'crm.lead':
			lead_obj = self.env['crm.lead']

			lead_search = lead_obj.search([('id', '=', active_id)])

			self.lead_id = lead_search
			self.lead_team_id = lead_search.team_id

			for lead_seq in lead_search.stage_id:
				stage_obj = self.env['crm.stage'].search([('sequence', '<' , lead_seq.sequence )])
				
				stage_get = self.env['crm.stage'].browse(stage_obj)

				self.stage_sequence = lead_search.stage_id.sequence
				self.company_id = lead_search.company_id.id

		elif active_model == 'odes.part':
			part_obj = self.env['odes.part']
			lead_obj = self.env['crm.lead']
			part_search = part_obj.search([('id', '=', active_id)])

			# lead_search = lead_obj.search([('id', '=', active_id)])
			lead_search = part_search.lead_id
			self.lead_id = part_search.lead_id
			self.lead_team_id = lead_search.team_id

			for lead_seq in lead_search.stage_id:
				stage_obj = self.env['crm.stage'].search([('sequence', '<' , lead_seq.sequence )])
				if self.lead_id.is_iconnexion:
					stage_obj = self.env['crm.stage'].search([('company_ids', 'in' , [3] )]) #only stage in iconnexion
					
				stage_get = self.env['crm.stage'].browse(stage_obj)

				self.stage_sequence = lead_search.stage_id.sequence
				self.company_id = lead_search.company_id.id

	def action_change_stage(self):
		if self.stage_id == self.lead_id.stage_id:
			raise UserError(_('Sorry, the stage cannot be the same as the previous stage'))

		if not self.stage_id == self.lead_id.stage_id:
			self.lead_id.with_context({'odes_view': 1,'icon_view': 1}).write({
				'stage_id': self.stage_id.id
				})

			partner_ids = []
			# if self.product_id.product_brand_id:
			# 	for partner_id in self.sale_line_id.product_id.product_brand_id.icon_product_partner_manager_ids:
			# 		partner_ids.append(partner_id.id)
			self.lead_id.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
								'iconnexion_custom.crm_change_stage',
							values={'crm': self.lead_id,'reason':self.reason},
							subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
							partner_ids=partner_ids,
							subject='Stage Change '+ self.lead_id.name,                            
					) 

			return self.write_to_history()


	def write_to_history(self):
		odes_stage_obj = self.env['odes.crm.stage']
		last_stage = odes_stage_obj.search([('lead_id', '=', self.lead_id.id)], order='start_datetime desc', limit=1)

		last_stage.write({
			'backward_reason':self.reason
			})

		odes_dip_obj = self.env['icon.design.in.progress']
		odes_dip_ids = odes_dip_obj.search([('status','=','Bidding: Order Win'),('crm_icon_dip_id','=',self.lead_id.id)])
		odes_dip_ids.write({'is_check':False})
		odes_dip2_ids = odes_dip_obj.search([('status','=','Design: Order Win'),('crm_icon_dip_design_id','=',self.lead_id.id)])
		odes_dip2_ids.write({'is_check':False})
		odes_dip3_ids = odes_dip_obj.search([('status','=','Order Win'),('crm_icon_dip_trading_id','=',self.lead_id.id)])
		odes_dip3_ids.write({'is_check':False})
		odes_dip_obj = self.env['icon.design.in.progress']
		odes_dip_ids = odes_dip_obj.search([('status','=','Bidding: Order Lost'),('crm_icon_dip_id','=',self.lead_id.id)])
		odes_dip_ids.write({'is_check':False})
		odes_dip2_ids = odes_dip_obj.search([('status','=','Design: Order Lost'),('crm_icon_dip_design_id','=',self.lead_id.id)])
		odes_dip2_ids.write({'is_check':False})
		odes_dip3_ids = odes_dip_obj.search([('status','=','Order Lost'),('crm_icon_dip_trading_id','=',self.lead_id.id)])
		odes_dip3_ids.write({'is_check':False})

class CrmLeadLost(models.TransientModel):
	_inherit = "crm.lead.lost"

	def action_lost_reason_apply(self):
		leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
		lost_stage = leads._stage_find(domain=[('name', '=', 'Lost')])
		odes_dip_obj = self.env['icon.design.in.progress']
		odes_dip_ids = odes_dip_obj.search([('status','=','Bidding: Order Lost'),('crm_icon_dip_id','=',leads.id)])
		odes_dip_ids.write({'is_check':True, 'check_datetime':datetime.now()})
		odes_dip2_ids = odes_dip_obj.search([('status','=','Design: Order Lost'),('crm_icon_dip_design_id','=',leads.id)])
		odes_dip2_ids.write({'is_check':True, 'check_datetime':datetime.now()})
		odes_dip3_ids = odes_dip_obj.search([('status','=','Order Lost'),('crm_icon_dip_trading_id','=',leads.id)])
		odes_dip3_ids.write({'is_check':True, 'check_datetime':datetime.now()})
		if leads.is_iconnexion:
			return leads.with_context({'icon_view' : 1,}).write({'lost_reason': self.reason, 'stage_id': lost_stage.id, 'probability': 0,})
		else:
			return leads.write({'lost_reason': self.reason, 'active': False, 'probability': 0,})