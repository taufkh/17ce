
import logging
import threading
from datetime import date, datetime, timedelta
from psycopg2 import sql

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.addons.phone_validation.tools import phone_validation
from collections import OrderedDict, defaultdict
from dateutil.parser import parse


class Lead(models.Model):
    _inherit = 'crm.lead'
    _order = 'stage_latest_update, write_date, type, stage_id'

    _sql_constraints = [
    #    ('name_company_uniq', 'unique (name,company_id)', 'The name of the Opportunity/Lead must be unique per company!')
    ]

    partner_id = fields.Many2one(
        'res.partner', string='Customer', index=True, tracking=10,
        domain="['|', ('company_id', '=', False), '&', ('company_id', '=', company_id), '|', ('user_id', '=', user_id), ('user_id', '=', False)]",
        help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")

    attachment_count = fields.Integer(string='CRM Attachment Count', compute='_compute_count_attachment')
    crm_attachment_ids = fields.One2many('ir.attachment', 'crm_lead_id', 'Attachment')
    odes_stage_ids = fields.One2many('odes.crm.stage', 'lead_id', 'Stages History')
    minutes_record = fields.Text('Minutes Record')
    possibility = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')], string='Possibility', default='1')
    odes_lead_history_ids = fields.One2many('odes.crm.lead.history', 'lead_history_id', 'Possibility History')
    crm_lead_history_ids = fields.One2many('odes.lead.history', 'crm_lead_histoy_id', 'Lead History')
    stage_total_days = fields.Integer('Total Days', compute='action_total_days')
    stage_latest_update = fields.Integer('Latest Update Days', compute='action_latest_update', store=True)
    odes_revenue_history_ids = fields.One2many('odes.revenue.history', 'crm_lead_revenue_history_id', 'Revenue History')
    event_ids = fields.One2many('calendar.event', 'opportunity_id', 'Meeting Records')
    end_partner_char = fields.Char(string='End Customer (Text)')
    is_iconnexion = fields.Boolean(string="iConnexion Company", compute='compute_is_iconnexion', store=True)

    @api.depends('company_id')
    def compute_is_iconnexion(self):
        for lead in self:
            company_name = lead.company_id.name
            if company_name and 'iconnexion' in company_name.lower():
                lead.is_iconnexion = True
            else:
                lead.is_iconnexion = False

    # currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id, tracking=True)
    def _get_first_odes_currency(self):
        # v16: use a savepoint so that an UndefinedTable error (raised when the
        # M2M relation table res_company_res_currency_rel doesn't exist yet
        # during _auto_init) rolls back without aborting the outer transaction.
        try:
            with self.env.cr.savepoint():
                if self.env.company.odes_currency_ids.ids:
                    return self.env.company.odes_currency_ids.ids[0]
        except Exception:
            pass
        return False

    def _get_all_odes_currency(self):
        domain = []
        try:
            with self.env.cr.savepoint():
                if len(self.env.company.odes_currency_ids.ids) > 0:
                    domain = [('id', 'in', self.env.company.odes_currency_ids.ids)]
        except Exception:
            pass
        return domain


    currency_id = fields.Many2one('res.currency', 'Lead Currency', default=_get_first_odes_currency, domain=_get_all_odes_currency, tracking=True)
    currency_revenue = fields.Monetary('Expected Revenue (Currency)', currency_field='currency_id', tracking=True)
    currency_rate = fields.Float(compute='_compute_current_rate', string='Currency Rate', digits=0, store=True)
    expected_revenue2 = fields.Monetary(related='expected_revenue', string='Expected Revenue (Converted)', currency_field='company_currency')

    lost_reason = fields.Char('Lost Reason Note')
    is_sf = fields.Boolean('Sales Figure') ###NOT USED
    sf_count = fields.Integer('Numbers of Sales Figure', compute='_compute_sale_data') ###NOT USED
    is_odes = fields.Boolean('ODES Company')

    project_name = fields.Char('Project Name')
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
    ], 'Application (Legacy)')
    application_id = fields.Many2one('odes.application', string='Application')
    end_partner_id = fields.Many2one('res.partner', string='End Customer', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    end_product_id = fields.Many2one('product.product', string='End Product')
    contract_site = fields.Char('Contract Manufacturing Company/Site')
    design_location = fields.Char('Design Location')
    annual_qty = fields.Float('Annual Qty')
    mass_schedule_date = fields.Date('Mass Production Schedule')
    pilot_qty = fields.Float('Pilot Run Qty')
    pilot_schedule_date = fields.Date('Pilot Run Schedule Date')
    project_status = fields.Char('Project Status')
    project_lifespan = fields.Char('Project Lifespan')
    estimated_closing_date = fields.Date('Estimated Closing Date')
    project_s = fields.Char('S') ###NOT USED (WRONG)
    odes_competitor_ids = fields.One2many('odes.competitor', 'lead_id', 'Competitor Information')
    odes_part_ids = fields.One2many('odes.part', 'lead_id', 'Part Information')

    source = fields.Selection([
        ('existing_clients', 'Existing Clients'),
        ('supplier', 'Supplier'),
        ('e_commerce', 'e-Commerce'),
        ('phone_call', 'Phone Call'),
        ('online_chat', 'Online Chat'),
        ('customer_referrals', 'Customer Referrals'),
        ('website_email', 'Website / Email'),
        ('social_media', 'Social Media'),
        ('digital_advertising', 'Digital Advertising'),
        ('events_shows', 'Events / Shows'),
        ('direct_contact', 'Direct Contact'),
    ], 'Lead Source Type')
    social_media = fields.Selection([
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('wechat', 'WeChat'),
        ('youtube', 'YouTube'),
    ], 'Social Media')

    lead_stage_id = fields.Many2one('odes.lead.stage', 'Lead Stages', tracking=True)

    end_product_display_name = fields.Char('End Product (Display)')


    @api.model_create_multi
    def create(self, values_list):
        records = super(Lead, self).create(values_list)
        for vals, rec in zip(values_list, records):
            rec.onwrite_possibility()
            if vals.get('type') == 'lead':
                rec.lead_create_history()
            else:
                rec.onwrite_stage_id()
                rec.onwrite_expected_revenue()
            rec._onchage_company_id()
        return records

    def write(self, vals):
        context = dict(self._context or {})
        for lead in self:
            if 'stage_id' in vals:
                new_value = vals['stage_id']
                old_value = lead.stage_id.id
                new_value_search = self.env['crm.stage'].browse(new_value)
                new_sequence = new_value_search.sequence
                old_sequence = lead.stage_id.sequence

                #if new_sequence <= old_sequence and not context.get('odes_view'):
                   # raise UserError(_('Sorry, you cannot move the Stage backward.\nPlease use the "Stage Backward" button instead inside the form.'))

            if vals.get('lost_reason'):
                if lead.type == 'opportunity':
                    lead.with_context({'lost': 1}).onwrite_stage_id()
                else:
                    odes_history_obj = self.env['odes.lead.history']
                    if lead.crm_lead_history_ids:
                        last_stage = odes_history_obj.search([('crm_lead_histoy_id', '=', lead.id)], order='id desc', limit=1)
                        last_stage.end_datetime = datetime.now()
                    odes_history_obj.create({'crm_lead_histoy_id': self.id, 'status': 'Lost'})

        res = super(Lead, self).write(vals)
        for lead in self:
            if 'stage_id' in vals:
                lead.onwrite_stage_id()

        return res

    @api.depends('order_ids.state', 'order_ids.currency_id', 'order_ids.amount_untaxed', 'order_ids.date_order', 'order_ids.company_id')
    def _compute_sale_data(self):
        res = super(Lead, self)._compute_sale_data()
        ###NOT USED
        # for lead in self:
        #     lead.sf_count = lead.quotation_count
        for lead in self:
            total = 0.0
            quotation_cnt = 0
            sale_order_cnt = 0
            quotation_total = 0
            quotation_total_expected_revenue = 0
            company_currency = lead.company_currency or self.env.company.currency_id
            for order in lead.order_ids:
                if order.state in ('draft', 'sent', 'done'): #'draft', 'sent'
                    quotation_cnt += 1
                    # lead.is_odes and order.is_current
                    if lead.is_odes and order.is_current:
                        quotation_total += order.currency_id._convert(order.amount_total, lead.currency_id, order.company_id, order.date_order or fields.Date.today())
                        quotation_total_expected_revenue += order.currency_id._convert(order.amount_total, company_currency, order.company_id, order.date_order or fields.Date.today())
                if order.state == 'sale': #'draft', 'sent', 'cancel'
                    sale_order_cnt += 1
                    total += order.currency_id._convert(order.amount_total, lead.currency_id, order.company_id, order.date_order or fields.Date.today())
            lead.sale_amount_total = total
            lead.quotation_count = quotation_cnt
            lead.sale_order_count = sale_order_cnt
            if quotation_total > 0:
                lead.currency_revenue = quotation_total
                lead.expected_revenue = quotation_total_expected_revenue

        return res

    def action_view_sale_quotation(self):
        res = super(Lead, self).action_view_sale_quotation()
        res['context'] = {
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id,
            # 'default_so_type': 'sf',
        }
        res['domain'] = [('opportunity_id', '=', self.id), ('state', 'in', ['draft', 'sent', 'done'])]
        quotations = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent', 'done'))
        if len(quotations) == 1:
            res['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            res['res_id'] = quotations.id

        return res

    def get_attachment(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Attachment',
            'view_mode': 'kanban,form',
            'res_model': 'ir.attachment',
            'domain': [('crm_lead_id', '=', self.id)],
            'context': {'default_crm_lead_id':self.id, 'form_view_ref': 'odes_custom.odes_ir_attachment_view_form', 'kanban_view_ref':'odes_custom.odes_ir_attachment_kanban_form'}
        }

    def _compute_count_attachment(self):
        for crm_lead in self:
            crm_lead.attachment_count = self.env['ir.attachment'].search_count(
                [('crm_lead_id', '=', self.id)])

    @api.depends('currency_id')
    def _compute_current_rate(self):
        date = fields.Date.today()
        company = self.env.company
        for lead in self:
            currency_rates = lead.currency_id._get_rates(company, date)
            lead.currency_rate = currency_rates.get(lead.currency_id.id) or 1.0

    @api.onchange('currency_id', 'currency_revenue')
    def _onchage_revenue(self):
        if self.currency_id and self.currency_revenue:
            new_revenue = self.currency_revenue / self.currency_rate
            self.expected_revenue = self.expected_revenue2 = new_revenue
        else:
            self.expected_revenue = self.expected_revenue2 = 0.0

    @api.onchange('company_id')
    def _onchage_company_id(self):
        ###NOT USED
        # self.is_sf = self.company_id.is_sf
        self.is_odes = self.company_id.is_odes

    def onwrite_stage_id(self):
        context = dict(self._context or {})
        odes_stage_obj = self.env['odes.crm.stage']
        if self.odes_stage_ids:
            last_stage = odes_stage_obj.search([('lead_id', '=', self.id)], order='start_datetime desc', limit=1)
            last_stage.end_datetime = datetime.now()
        if context.get('lost'):
            odes_stage_obj.create({'lead_id': self.id, 'stage_name': 'Lost'})
        else:
            odes_stage_obj.create({'lead_id': self.id, 'stage_name': self.stage_id.name})

    def onwrite_possibility(self):
        odes_history_obj = self.env['odes.crm.lead.history']
        odes_history_obj.create({'lead_history_id': self.id, 'possibility': self.possibility})

    def onwrite_expected_revenue(self):
        odes_history_obj = self.env['odes.revenue.history']
        odes_history_obj.create({'crm_lead_revenue_history_id': self.id, 'amount': self.currency_revenue})

    @api.model
    def action_dashboard_redirect(self):
        return self.env.ref('odes_custom.odes_dashboard').read()[0]

    def action_view_sale_order(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['context'] = {
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id,
        }
        action['domain'] = [('opportunity_id', '=', self.id), ('state', 'not in', ('draft', 'sent', 'cancel', 'done'))]
        orders = self.mapped('order_ids').filtered(lambda l: l.state not in ('draft', 'sent', 'cancel', 'done'))
        if len(orders) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = orders.id
        return action

    ###CRM Dashboard Button###
    def get_dashboard_ctx(self):
        user = self.env.user
        context = dict(self._context or {})
        users_ids_search = False
        if not context.get('user_ctx') or context.get('user_ctx') == 'false':
            if user._is_manager():
                self.env.cr.execute("""
                    SELECT ru.id
                    from res_users ru
                    where ru.active = True and ru.share = False
                """)
                users_res = self.env.cr.fetchall()
                users_ids = tuple([x[0] for x in users_res])
                users_ids_search = users_ids
                users_ids_search += False,
            else:
                users_ids = tuple([user.id])
        else:
            users_ids = tuple([int(context['user_ctx'])])
        if not users_ids_search:
            users_ids_search = users_ids

        if not context.get('company_ctx') or context.get('company_ctx') == 'false':
            # companies_ids = tuple(user.company_ids.ids)
            companies_ids = []
            for comp in user.company_ids:
                if not comp.is_odes:
                    companies_ids.append(comp.id)
            companies_ids = tuple(companies_ids)
        else:
            companies_ids = tuple([int(context['company_ctx'])])

        return users_ids_search, companies_ids

    @api.model
    def action_crm_active_lead(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', True)]
        return action

    @api.model
    def action_crm_active_lead_l7(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', True), ('date_open', '>=', now_l7)]
        return action

    @api.model
    def action_crm_active_lead_g7(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', True), ('date_open', '<', now_l7)]
        return action

    @api.model
    def action_crm_active_opportunity(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.is_won', '=', False)]
        return action

    @api.model
    def action_crm_active_opportunity_l7(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.is_won', '=', False), ('date_open', '>=', now_l7)]
        return action

    @api.model
    def action_crm_active_opportunity_g7(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.is_won', '=', False), ('date_open', '<', now_l7)]
        return action

    @api.model
    def action_crm_outstanding_won(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.is_won', '=', True)]
        return action

    @api.model
    def action_crm_outstanding_lost(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', False), ('probability', '<=', 0)]
        return action


    def get_dashboard_ctx2(self):
        user = self.env.user
        context = dict(self._context or {})
        self.env.cr.execute("""
            SELECT ru.id
            from res_users ru
            where ru.active = True and ru.share = False
        """)
        users_res = self.env.cr.fetchall()
        users_ids = tuple([x[0] for x in users_res])
        users_ids_search = users_ids
        users_ids_search += False,
            
        companies_ids = []
        for comp in user.company_ids:
            if comp.is_odes:
                companies_ids.append(comp.id)
        companies_ids = tuple(companies_ids)

        return users_ids_search, companies_ids

    @api.model
    def odes_action_crm_active_lead(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx2()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', True)]
        return action

    @api.model
    def odes_action_crm_active_lead_l7(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx2()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', True), ('date_open', '>=', now_l7)]
        return action

    @api.model
    def odes_action_crm_active_lead_g7(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx2()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', True), ('date_open', '<', now_l7)]
        return action

    @api.model
    def odes_action_lead_lost(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx2()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', False), ('probability', '<=', 0)]
        return action

    @api.model
    def odes_action_crm_active_prospect(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx2()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.name', '=', 'Prospect')]
        return action

    @api.model
    def odes_action_crm_active_opportunity(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx2()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.name', '=', 'Opportunity')]
        return action

    @api.model
    def odes_action_crm_active_report(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx2()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.name', '=', 'Report')]
        return action

    @api.model
    def odes_action_crm_active_pending(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx2()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.name', '=', 'Pending')]
        return action

    @api.model
    def odes_action_crm_outstanding_won(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx2()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.is_won', '=', True)]
        return action

    @api.model
    def odes_action_crm_outstanding_lost(self):
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        user = self.env.user
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        context = dict(self._context or {})
        new_ctx = self.with_context(context).get_dashboard_ctx2()
        users_ids = new_ctx[0]
        companies_ids = new_ctx[1]
        action['domain'] = [('user_id', 'in', users_ids), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', False), ('probability', '<=', 0)]
        return action
    ###CRM Dashboard Button###

    def action_lead_history_wizard(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'Input Reason',
            'res_model': 'odes.crm.lead.history.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self._context.get('active_id'), 'active_model': self._context.get('active_model')},
        }

    @api.depends('stage_id')
    def action_latest_update(self):
        odes_stage_obj = self.env['odes.crm.stage']
        odes_stage2_obj = self.env['odes.lead.history']
        now = parse((datetime.now()+timedelta(hours=8)).strftime('%Y-%m-%d'))
        for lead in self:
            latest_days = 0
            start_datetime = False
            if lead.type == 'opportunity':
                start_datetime = odes_stage_obj.search([('lead_id', '=', lead.id)], order='id desc', limit=1).start_datetime
            
            elif lead.type == 'lead':
                # v16: date_open may be False when no date is set; guard against TypeError
                _hist_dt = odes_stage2_obj.search([('crm_lead_histoy_id', '=', lead.id)], order='id desc', limit=1).start_datetime
                start_datetime = _hist_dt or (lead.date_open - timedelta(hours=8) if lead.date_open else False)
                
            if start_datetime:
                latest_days = (now - parse(str(start_datetime))).days + 1
            else:
                latest_days = 1

            lead.stage_latest_update = latest_days


    def action_total_days(self):
        odes_stage_obj = self.env['odes.crm.stage']
        odes_stage2_obj = self.env['odes.lead.history']
        now = parse((datetime.now()+timedelta(hours=8)).strftime('%Y-%m-%d'))
        for lead in self:
            total_days = 0
            start_datetime = False
            end_datetime = False
            if lead.type == 'opportunity':
                start_datetime = odes_stage_obj.search([('lead_id', '=', lead.id)], order='id', limit=1).start_datetime
                if lead.stage_id.is_won:
                    end_datetime = odes_stage_obj.search([('lead_id', '=', lead.id)], order='id desc', limit=1).start_datetime
                else:
                    end_datetime = odes_stage_obj.search([('lead_id', '=', lead.id)], order='id desc', limit=1).end_datetime
            elif lead.type == 'lead':
                start_datetime = odes_stage2_obj.search([('crm_lead_histoy_id', '=', lead.id)], order='id', limit=1).start_datetime or lead.date_open - timedelta(hours=8)
                end_datetime = odes_stage2_obj.search([('crm_lead_histoy_id', '=', lead.id)], order='id desc', limit=1).end_datetime
            # for stage in lead.odes_stage_ids:
            #     if not start_datetime or start_datetime != False and stage.start_datetime != False and stage.start_datetime < start_datetime:
            #         start_datetime = stage.start_datetime
            #     if not end_datetime or end_datetime != False and stage.end_datetime != False and stage.end_datetime > end_datetime:
            #         end_datetime = stage.end_datetime
                    
            if start_datetime and end_datetime:
                total_days = (parse(str(end_datetime)) - parse(str(start_datetime))).days + 1
            elif start_datetime:
                total_days = (now - parse(str(start_datetime))).days + 1
            else:
                total_days = 1

            lead.stage_total_days = total_days

    def lead_create_history(self):
        odes_stage_obj = self.env['odes.lead.history']
        if self.crm_lead_history_ids:
            last_stage = odes_stage_obj.search([('crm_lead_histoy_id', '=', self.id)], order='start_datetime desc', limit=1)
            last_stage.end_datetime = datetime.now()

        odes_stage_obj.create({'crm_lead_histoy_id': self.id, 'status': 'Created'})

    def action_revenue_history_wizard(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'Input Reason',
            'res_model': 'odes.revenue.history.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self._context.get('active_id'), 'active_model': self._context.get('active_model')},
        }

    def action_odes_crm_backward_stage(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'Backward Stages',
            'res_model': 'odes.crm.backward.stage.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self._context.get('active_id'), 'active_model': self._context.get('active_model')},
        }

    @api.constrains('type', 'expected_revenue', 'stage_id')
    def _check_revenue(self):
        for lead in self:
            if lead.type == 'opportunity' and lead.expected_revenue <= 0 and lead.stage_id.is_revenue:
                raise ValidationError(_('The Expected Revenue of the Opportunity can\'t be 0 or negative.'))

    @api.constrains('stage_id')
    def _check_stages(self):
        sale_obj = self.env['sale.order']
        for lead in self:
            if lead.stage_id.is_need_so:
                order1 = sale_obj.search([('opportunity_id', '=', lead.id), ('state', '!=', 'cancel')], limit=1)
                if not order1:
                    raise ValidationError(_('Please input a Quotation to change the stage into "%s".') % (lead.stage_id.name))
            if lead.stage_id.is_confirm_so:
                order2 = sale_obj.search([('opportunity_id', '=', lead.id), ('state', 'in', ('sale', 'done'))], limit=1)
                if not order2:
                    raise ValidationError(_('Please confirm the Quotation to change the stage into "%s".') % (lead.stage_id.name))

    def action_copy_end_product(self):
        records = self.env['crm.lead'].search([('end_product_id', '!=', False)])
        for record in records:
            record.write({'end_product_display_name': record.end_product_id.display_name})

        partnos = self.env['odes.part'].search([('name', '!=', False)])
        for partno in partnos:
            product_id = self.env['product.product'].search([('default_code', '=', partno.name), ('active', '=', True)], limit=1)
            if(product_id):
                partno.write({'product_id': product_id.id})

    def action_copy_end_application(self):
        records = self.env['crm.lead'].search([('application', '!=', False)])
        for record in records:
            application_id = self.env['odes.application'].search([('name_small', '=', record.application)], limit=1)
            if(application_id):
                record.write({'application_id': application_id.id})

class CrmLeadProject(models.Model):
    _inherit = "crm.lead"

    project_ids = fields.One2many('project.project', 'lead_id', 'Projects')
    project_count = fields.Integer('Project Count', compute='_get_project_count')

    def write(self, vals):
        res = super(CrmLeadProject, self).write(vals)
        for lead in self:
            if vals.get('stage_id'):
                if lead.company_id.is_project and self.env['crm.stage'].browse(vals['stage_id']).is_won:
                    if not lead.project_ids.ids:
                        project_ids = lead.create_project()
                        
        return res

    def _get_project_count(self):
        for lead in self:
            lead.project_count = len(lead.project_ids.ids) or 0

    def action_set_won_rainbowman(self):
        res = super(CrmLeadProject, self).action_set_won_rainbowman()
        for lead in self:
            if lead.company_id.is_project:
                if not lead.project_ids.ids:
                    project_ids = lead.create_project()

        return res

    def create_project(self):
        # action = self.env["ir.actions.actions"]._for_xml_id("project.open_view_project_all")
        project_task_obj = self.env['project.task.type'].sudo()
        project_obj = self.env['project.project']
        project_ids = []
        for lead in self:
            project = project_obj.create({
                'name': lead.partner_name or lead.name,
                'lead_id': lead.id,
                'partner_id': lead.partner_id.id,
            })

            project_ids.append(project.id)

        for task in project_task_obj.search([]):
            task.write({'project_ids': task.project_ids.ids + project_ids})
        return project_ids

    def action_crm_project_view(self):
        # action = self.env["ir.actions.actions"]._for_xml_id("project.open_view_project_all")
        # action['domain'] = [('lead_id', '=', self.id)]
        action = {
            'name': _('Projects'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'project.project',
            'res_id': self.project_ids and self.project_ids[0].id or False,
            'context': {'default_lead_id': self.id, 'default_name': self.name,},
        }

        return action


class CrmLeadCompany(models.Model):
    _inherit = "crm.lead"

    stage_id = fields.Many2one(
        'crm.stage', string='Stage', index=True, tracking=True,
        compute='_compute_stage_id', readonly=False, store=True,
        copy=False, group_expand='_read_group_stage_ids', ondelete='restrict',
        domain="[('company_ids', '=', company_id)]")

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # # retrieve team_id from the context and write the domain
        # # - ('id', 'in', stages.ids): add columns that should be present
        # # - OR ('fold', '=', False): add default columns that are not folded
        # # - OR ('team_ids', '=', team_id), ('fold', '=', False) if team_id: add team columns that are not folded
        # team_id = self._context.get('default_team_id')
        # if team_id:
        #     search_domain = ['|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        # else:
        #     search_domain = ['|', ('id', 'in', stages.ids), ('team_id', '=', False)]
        search_domain = ['|', ('id', 'in', stages.ids), ('company_ids', 'in', tuple([self.env.company.id]))]

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    def _stage_find(self, team_id=False, domain=None, order='sequence'):
        # """ Determine the stage of the current lead with its teams, the given domain and the given team_id
        #     :param team_id
        #     :param domain : base search domain for stage
        #     :returns crm.stage recordset
        # """
        # # collect all team_ids by adding given one, and the ones related to the current leads
        # team_ids = set()
        # if team_id:
        #     team_ids.add(team_id)
        # for lead in self:
        #     if lead.team_id:
        #         team_ids.add(lead.team_id.id)
        # # generate the domain
        # if team_ids:
        #     search_domain = ['|', ('team_id', '=', False), ('team_id', 'in', list(team_ids))]
        # else:
        #     search_domain = [('team_id', '=', False)]
        # # AND with the domain in parameter
        company_ids = []
        for lead in self:
            if lead.company_id:
                company_ids.append(lead.company_id.id)
        if not company_ids:
            company_ids = [self.env.company.id]
        search_domain = [('company_ids', 'in', tuple(company_ids))]
        if domain:
            search_domain += list(domain)
        # perform search, return the first found
        return self.env['crm.stage'].search(search_domain, order=order, limit=1)


class CrmLostReason(models.Model):
    _inherit = "crm.lost.reason"
    _order = "is_input, id, name"

    is_input = fields.Boolean('Input', default=False)


class LeadHistory(models.Model):
    _name = 'odes.crm.lead.history'
    _description = "Opportunity History"
    _order = 'id desc'

    lead_history_id = fields.Many2one('crm.lead', 'CRM Lead')
    possibility = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')], string='Possibility')
    history_reason = fields.Char('Reason')



class OdesLeadHistory(models.Model):
    _name = 'odes.lead.history'
    _description = "Lead History"
    _order = 'id desc'

    crm_lead_histoy_id = fields.Many2one('crm.lead', 'CRM Lead')
    status = fields.Char('Status')
    start_datetime = fields.Date('Start Time', default=fields.Datetime.now)
    end_datetime = fields.Date('End Time')
    days_count = fields.Integer(string='Days', compute="_action_count_date")

    def _action_count_date(self):
        now = parse((datetime.now()+timedelta(hours=8)).strftime('%Y-%m-%d'))
        self.days_count = 0
        for count in self:
            day_start = count.start_datetime and parse(str(count.start_datetime)) or now
            day_end = count.end_datetime and parse(str(count.end_datetime)) or now
            
            total = (day_end - day_start).days + 1
            if count.crm_lead_histoy_id.type == 'opportunity' and not count.end_datetime:
                total = 1
                
            count.days_count = total

class OdesRevenueHistory(models.Model):
    _name = 'odes.revenue.history'
    _description = "Expected Revenue History"
    _order = 'id desc'

    crm_lead_revenue_history_id = fields.Many2one('crm.lead', 'CRM Lead')
    amount = fields.Float('Amount')
    change_reason = fields.Char('Reason')


class OdesCompetitor(models.Model):
    _name = "odes.competitor"
    _description = 'Competitor'

    name = fields.Char('Competitor Information')
    lead_id = fields.Many2one('crm.lead', 'Lead')
    manufacture = fields.Char('Manufacture')
    price = fields.Float('Competitor Price / Target Price')


class OdesPart(models.Model):
    _name = "odes.part"
    _description = 'Part'
    product_id = fields.Many2one('product.product',string='Part No.',)
    name = fields.Char(string='Part Number (Text)',)
    lead_id = fields.Many2one('crm.lead', 'Lead')
    manufacture = fields.Char('Manufacture')
    price = fields.Float('Cost')

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            rec.name = rec.product_id.default_code
            rec.manufacture = rec.product_id.product_brand_id.name
            rec.price = rec.product_id.standard_price
