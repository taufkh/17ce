# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from datetime import date, datetime, timedelta


class Lead2OpportunityPartner(models.TransientModel):
	_inherit = 'crm.lead2opportunity.partner'
	_description = 'Convert Lead to Opportunity (not in mass)'    

	end_partner_char = fields.Char(string='End Partner Char',
		compute='_compute_project', readonly=False, store=True, compute_sudo=False)

	def _convert_and_allocate(self, leads, user_ids, team_id=False):        
		#overwrite this function for icon approval
		#convert_opportunity_approve is a new function for approval
		self.ensure_one()

		for lead in leads:
			if lead.active and self.action != 'nothing':
				self._convert_handle_partner(
					lead, self.action, self.partner_id.id or lead.partner_id.id)

			if self.action == 'create':
				lead.convert_opportunity_approve(lead.partner_id.id, [], False)
			else:
				lead.convert_opportunity(lead.partner_id.id, [], False)

		leads_to_allocate = leads
		if not self.force_assignment:
			leads_to_allocate = leads_to_allocate.filtered(lambda lead: not lead.user_id)

		if user_ids:
			leads_to_allocate.handle_salesmen_assignment(user_ids, team_id=team_id)

	def action_apply(self):
		lead_history_obj = self.env['odes.lead.history']
		competitor_obj = self.env['odes.competitor']
		part_obj = self.env['odes.part']

		result_opportunities = self.env['crm.lead'].browse(self._context.get('active_ids', []))
		result_opportunities = result_opportunities and result_opportunities[0]
		result_opportunities.write({'currency_revenue': self.expected_revenue, 'possibility': self.possibility, 
			'currency_id': self.currency_id.id,})
		result_opportunities._onchage_revenue()

		lines1 = []
		for line1 in self.odes_competitor_ids:
			lines1.append(competitor_obj.create({
				'name': line1.name,
				'manufacture': line1.manufacture,
				'price': line1.price,
			}).id)

		lines2 = []
		for line2 in self.odes_part_ids:
			product_id = False
			if line2.product_id:
				product_id = line2.product_id.id
			lines2.append(part_obj.create({
				'name': line2.name,
				'manufacture': line2.manufacture,
				'price': line2.price,
				'product_id': product_id,
				'competitor_information': line2.competitor_information,
				'quoted_price':line2.quoted_price,
				'competitor_mpn': line2.competitor_mpn,
				'competitor_pricing': line2.competitor_pricing,
				'competitor_moq': line2.competitor_moq,
				'icon_date': line2.icon_date,
			}).id)

		result_opportunities.write({
			'project_name': self.project_name,
			'application': self.application,
			'end_partner_id': self.end_partner_id.id,
			'end_product_id': self.end_product_id.id,
			'contract_site': self.contract_site,
			'design_location': self.design_location,
			'annual_qty': self.annual_qty,
			'mass_schedule_date': self.mass_schedule_date,
			'pilot_qty': self.pilot_qty,
			'pilot_schedule_date': self.pilot_schedule_date,
			'project_status': self.project_status,
			'project_lifespan': self.project_lifespan,
			'estimated_closing_date': self.estimated_closing_date,
			'odes_competitor_ids': [(6, 0, lines1)],
			'odes_part_ids': [(6, 0, lines2)],
		})

		if self.name == 'merge':
			result_opportunity = self._action_merge()
		else:
			result_opportunity = self._action_convert()

		if result_opportunities.crm_lead_history_ids:
			last_stage = lead_history_obj.search([('crm_lead_histoy_id', '=', result_opportunities.id)], order='start_datetime desc', limit=1)
			last_stage.end_datetime = datetime.now()
		
		result_opportunities.onwrite_stage_id()
		result_opportunities.onwrite_possibility()
		result_opportunities.onwrite_expected_revenue()
		lead_history_obj.create({'crm_lead_histoy_id': result_opportunities.id, 'status': 'Converted to Opportunity'})

		return result_opportunity.redirect_lead_opportunity_view()

	@api.depends('lead_id')
	def _compute_project(self):
		for convert in self:
			convert.project_name = convert.lead_id.project_name
			convert.application = convert.lead_id.application
			convert.end_partner_id = convert.lead_id.end_partner_id.id
			convert.end_product_id = convert.lead_id.end_product_id.id
			convert.end_partner_char = convert.lead_id.end_partner_char
			convert.contract_site = convert.lead_id.contract_site
			convert.design_location = convert.lead_id.design_location
			convert.annual_qty = convert.lead_id.annual_qty
			convert.mass_schedule_date = convert.lead_id.mass_schedule_date
			convert.pilot_qty = convert.lead_id.pilot_qty
			convert.pilot_schedule_date = convert.lead_id.pilot_schedule_date
			convert.project_status = convert.lead_id.project_status
			convert.project_lifespan = convert.lead_id.project_lifespan
			convert.estimated_closing_date = convert.lead_id.estimated_closing_date
			convert.possibility = convert.lead_id.possibility
			lines1 = []
			for line1 in convert.lead_id.odes_competitor_ids:
				lines1.append((0, 0, {
					'name': line1.name,
					'manufacture': line1.manufacture,
					'price': line1.price,
				}))
			convert.odes_competitor_ids = lines1

			lines2 = []
			for line2 in convert.lead_id.odes_part_ids:
				product_id = False
				if line2.product_id:
					product_id = line2.product_id.id
				lines2.append((0, 0, {
					'name': line2.name,
					'manufacture': line2.manufacture,
					'price': line2.price,
					'product_id': product_id,
					'competitor_information': line2.competitor_information,
					'quoted_price':line2.quoted_price,
					'competitor_mpn': line2.competitor_mpn,
					'competitor_pricing': line2.competitor_pricing,
					'competitor_moq': line2.competitor_moq,
					'icon_date': line2.icon_date,
				}))
			convert.odes_part_ids = lines2



class OdesPart(models.TransientModel):
	_inherit = "odes.part.wizard"
	_description = 'Part Wizard'


	product_id = fields.Many2one('product.product', 'Products')
	competitor_information = fields.Char('Competitor')
	competitor_price = fields.Float('Competitor Price / Target Price')
	quoted_price = fields.Float('Quoted Price',digits='Product Price')
	competitor_mpn = fields.Char('Competitor MPN')
	competitor_pricing = fields.Char('Competitor Pricing')
	competitor_moq = fields.Char('Competitor MOQ')
	icon_date = fields.Date('Date')