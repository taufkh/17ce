# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from datetime import date, datetime, timedelta


class OdesLead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'
    _description = 'Convert Lead to Opportunity (not in mass)'

    possibility = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')], string='Possibility')
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id)
    expected_revenue = fields.Monetary('Expected Revenue', currency_field='currency_id')

    company_id = fields.Many2one('res.company', 'Company', compute='_compute_company_id', store=True)
    is_odes = fields.Boolean('ODES Company')

    project_name = fields.Char('Project Name',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    application = fields.Selection([
        ('agriculture', 'Agriculture'), ('automotive', 'Automotive & EV'),
        ('computers', 'Computers & Peripherals'), ('home', 'Home Appliance'),
        ('in_building', 'In-Building'), ('industrial', 'Industrial Automation'),
        ('lighting', 'Lighting'), ('medical', 'Medical'),
        ('network', 'Network Infrastructure'), ('oil', 'Oil, Gas & Energy'),
        ('electronics', 'Personal Electronics'), ('rail', 'Rail & Mass Transit'),
        ('retail', 'Retail & Warehousing'), ('security', 'Security & Surveillance'),
        ('smart_energy', 'Smart Energy & Metering'), ('space', 'Space, Avionics & Defense'),
        ('test', 'Test & Instrumentation'), ('others', 'Others'),
    ], 'Application',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    end_partner_id = fields.Many2one('res.partner', string='End Customer', domain="['|', ('company_id', '=', False), '&', ('company_id', '=', company_id), ('user_id', '=', user_id)]",
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    end_product_id = fields.Many2one('product.product', string='End Product',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    contract_site = fields.Char('Contract Manufacturing Company/Site',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    design_location = fields.Char('Design Location',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    annual_qty = fields.Float('Annual Qty',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    mass_schedule_date = fields.Date('Mass Production Schedule',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    pilot_qty = fields.Float('Pilot Run Qty',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    pilot_schedule_date = fields.Date('Pilot Run Schedule Date',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    project_status = fields.Char('Project Status',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    project_lifespan = fields.Char('Project Lifespan',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    estimated_closing_date = fields.Date('Estimated Closing Date',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    project_s = fields.Char('S',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False) ###NOT USED (WRONG)
    odes_competitor_ids = fields.One2many('odes.competitor.wizard', 'lead2opportunity_id', 'Competitor Information',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)
    odes_part_ids = fields.One2many('odes.part.wizard', 'lead2opportunity_id', 'Part Information',
        compute='_compute_project', readonly=False, store=True, compute_sudo=False)

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
            lines2.append(part_obj.create({
                'name': line2.name,
                'manufacture': line2.manufacture,
                'price': line2.price,
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

    @api.depends('duplicated_lead_ids')
    def _compute_name(self):
        for convert in self:
            convert.name = 'convert'

    @api.depends('user_id')
    def _compute_team_id(self):
        for convert in self:
            convert.team_id = convert.lead_id.team_id.id

    @api.depends('lead_id')
    def _compute_company_id(self):
        for convert in self:
            convert.company_id = convert.lead_id.company_id.id

    @api.depends('lead_id')
    def _compute_project(self):
        for convert in self:
            convert.project_name = convert.lead_id.project_name
            convert.application = convert.lead_id.application
            convert.end_partner_id = convert.lead_id.end_partner_id.id
            convert.end_product_id = convert.lead_id.end_product_id.id
            convert.contract_site = convert.lead_id.contract_site
            convert.design_location = convert.lead_id.design_location
            convert.annual_qty = convert.lead_id.annual_qty
            convert.mass_schedule_date = convert.lead_id.mass_schedule_date
            convert.pilot_qty = convert.lead_id.pilot_qty
            convert.pilot_schedule_date = convert.lead_id.pilot_schedule_date
            convert.project_status = convert.lead_id.project_status
            convert.project_lifespan = convert.lead_id.project_lifespan
            convert.estimated_closing_date = convert.lead_id.estimated_closing_date

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
                lines2.append((0, 0, {
                    'name': line2.name,
                    'manufacture': line2.manufacture,
                    'price': line2.price,
                }))
            convert.odes_part_ids = lines2


class OdesCompetitor(models.TransientModel):
    _name = "odes.competitor.wizard"
    _description = 'Competitor Wizard'

    name = fields.Char('Competitor Information')
    lead2opportunity_id = fields.Many2one('crm.lead2opportunity.partner', 'Lead')
    manufacture = fields.Char('Manufacture')
    price = fields.Float('Competitor Price / Target Price')


class OdesPart(models.TransientModel):
    _name = "odes.part.wizard"
    _description = 'Part Wizard'

    name = fields.Char('Part No.')
    lead2opportunity_id = fields.Many2one('crm.lead2opportunity.partner', 'Lead')
    manufacture = fields.Char('Manufacture')
    price = fields.Float('Cost')