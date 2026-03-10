from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from datetime import datetime, timedelta
import json

class WebsiteBackend(http.Controller):

    @http.route('/odes_custom/fetch_dashboard_data', type="json", auth='user')
    def fetch_dashboard_data(self, **post):
        user = request.env.user
        lead_obj = request.env['crm.lead']
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        results = {}

        users_ids_search = False
        if not post.get('user') or post.get('user') == 'false':
            if user._is_manager():
                request.env.cr.execute("""
                    SELECT ru.id
                    from res_users ru
                    where ru.active = True and ru.share = False
                """)
                users_res = request.env.cr.fetchall()
                users_ids = tuple([x[0] for x in users_res])
                users_ids_search = users_ids
                users_ids_search += False,
            else:
                users_ids = tuple([user.id])
        else:
            users_ids = tuple([int(post['user'])])
        if not users_ids_search:
            users_ids_search = users_ids

        if not post.get('company') or post.get('company') == 'false':
            # companies_ids = tuple(user.company_ids.ids)
            companies_ids = []
            for comp in user.company_ids:
                if not comp.is_odes:
                    companies_ids.append(comp.id)
            companies_ids = tuple(companies_ids)
        else:
            companies_ids = tuple([int(post['company'])])

        active_lead = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', True)])
        active_lead_l7 = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', True), ('date_open', '>=', now_l7)])
        active_lead_g7 = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', True), ('date_open', '<', now_l7)])
        active_opportunity = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.is_won', '=', False)])
        active_opportunity_l7 = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.is_won', '=', False), ('date_open', '>=', now_l7)])
        active_opportunity_g7 = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.is_won', '=', False), ('date_open', '<', now_l7)])
        outstanding_won = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.is_won', '=', True)])
        outstanding_lost = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', False), ('probability', '<=', 0)])

        request.env.cr.execute("""
            SELECT COALESCE(sum(l.expected_revenue), 0.0)
            from crm_lead l
            inner join crm_stage s on s.id = l.stage_id
            where l.user_id in %s and l.company_id in %s and l.type = 'opportunity' and l.active = True and (s.is_won = False or s.is_won isnull)
        """, (users_ids, companies_ids or (2, 3),))
        opportunity_revenue = '$'+'{:,.2f}'.format(request.env.cr.fetchone()[0])

        request.env.cr.execute("""
            SELECT COALESCE(sum(l.expected_revenue), 0.0)
            from crm_lead l
            inner join crm_stage s on s.id = l.stage_id
            where l.user_id in %s and l.company_id in %s and l.type = 'opportunity' and l.active = True and (s.is_won = False or s.is_won isnull) and date_open >= %s
        """, (users_ids, companies_ids or (2, 3), now_l7))
        opportunity_revenue_l7 = '$'+'{:,.2f}'.format(request.env.cr.fetchone()[0])

        request.env.cr.execute("""
            SELECT COALESCE(sum(l.expected_revenue), 0.0)
            from crm_lead l
            inner join crm_stage s on s.id = l.stage_id
            where l.user_id in %s and l.company_id in %s and l.type = 'opportunity' and l.active = True and (s.is_won = False or s.is_won isnull) and date_open < %s
        """, (users_ids, companies_ids or (2, 3), now_l7))
        opportunity_revenue_g7 = '$'+'{:,.2f}'.format(request.env.cr.fetchone()[0])

        request.env.cr.execute("""
            SELECT 
                CASE WHEN l.active = True then s.name else 'Lost' END as new_name,
                count(l.id) as total,
                cast(sum(l.expected_revenue) as money) as amount
            from crm_lead l
            inner join crm_stage s on s.id = l.stage_id
            where l.user_id in %s and l.company_id in %s and l.type = 'opportunity'
            group by l.active, new_name, s.id
            order by l.active desc, s.sequence
            limit 7
        """, (users_ids, companies_ids or (2, 3),))
        funnel_data = request.env.cr.dictfetchall()
        count = 0

        fname1 = ''
        fcount1 = 0
        fmoun1 = '$0.00'
        fname2 = ''
        fcount2 = 0
        fmoun2 = '$0.00'
        fname3 = ''
        fcount3 = 0
        fmoun3 = '$0.00'
        fname4 = ''
        fcount4 = 0
        fmoun4 = '$0.00'
        fname5 = ''
        fcount5 = 0
        fmoun5 = '$0.00'
        fname6 = ''
        fcount6 = 0
        fmoun6 = '$0.00'
        fname7 = ''
        fcount7 = 0
        fmoun7 = '$0.00'
        for funnel in funnel_data:
            count += 1
            if count == 1:
                fname1 = funnel['new_name']
                fcount1 = funnel['total']
                fmoun1 = funnel['amount']
            elif count == 2:
                fname2 = funnel['new_name']
                fcount2 = funnel['total']
                fmoun2 = funnel['amount']
            elif count == 3:
                fname3 = funnel['new_name']
                fcount3 = funnel['total']
                fmoun3 = funnel['amount']
            elif count == 4:
                fname4 = funnel['new_name']
                fcount4 = funnel['total']
                fmoun4 = funnel['amount']
            elif count == 5:
                fname5 = funnel['new_name']
                fcount5 = funnel['total']
                fmoun5 = funnel['amount']
            elif count == 6:
                fname6 = funnel['new_name']
                fcount6 = funnel['total']
                fmoun6 = funnel['amount']
            elif count == 7:
                fname7 = funnel['new_name']
                fcount7 = funnel['total']
                fmoun7 = funnel['amount']

        results = {
            'active_lead': active_lead,
            'active_lead_l7': active_lead_l7,
            'active_lead_g7': active_lead_g7,
            'active_opportunity': active_opportunity,
            'opportunity_revenue': opportunity_revenue,
            'active_opportunity_l7': active_opportunity_l7,
            'opportunity_revenue_l7': opportunity_revenue_l7,
            'active_opportunity_g7': active_opportunity_g7,
            'opportunity_revenue_g7': opportunity_revenue_g7,
            'outstanding_won': outstanding_won,
            'outstanding_lost': outstanding_lost,
            'funnel_data': funnel_data,

            'fname1': fname1,
            'fcount1': fcount1,
            'fmoun1': fmoun1,
            'fname2': fname2,
            'fcount2': fcount2,
            'fmoun2': fmoun2,
            'fname3': fname3,
            'fcount3': fcount3,
            'fmoun3': fmoun3,
            'fname4': fname4,
            'fcount4': fcount4,
            'fmoun4': fmoun4,
            'fname5': fname5,
            'fcount5': fcount5,
            'fmoun5': fmoun5,
            'fname6': fname6,
            'fcount6': fcount6,
            'fmoun6': fmoun6,
            'fname7': fname7,
            'fcount7': fcount7,
            'fmoun7': fmoun7,
        }
        return results

    @http.route('/odes_custom/fetch_dashboard_data2', type="json", auth='user')
    def fetch_dashboard_data2(self, **post):
        user = request.env.user
        lead_obj = request.env['crm.lead']
        now = (datetime.now()+timedelta(hours=8))
        now_l7 = (now-timedelta(days=8)).strftime('%Y-%m-%d 16:00:00')
        results = {}

        request.env.cr.execute("""
            SELECT ru.id
            from res_users ru
            where ru.active = True and ru.share = False
        """)
        users_res = request.env.cr.fetchall()
        users_ids = tuple([x[0] for x in users_res])
        users_ids_search = users_ids
        users_ids_search += False,

        companies_ids = []
        for comp in user.company_ids:
            if comp.is_odes:
                companies_ids.append(comp.id)
        companies_ids = tuple(companies_ids)

        active_lead = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', True)])
        active_lead_l7 = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', True), ('date_open', '>=', now_l7)])
        active_lead_g7 = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', True), ('date_open', '<', now_l7)])
        lead_lost = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', False), ('probability', '<=', 0)])

        active_prospect = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.name', '=', 'Prospect')])
        active_opportunity = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.name', '=', 'Opportunity')])
        active_report = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.name', '=', 'Report')])
        active_pending = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.name', '=', 'Pending')])
        outstanding_won = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.is_won', '=', True)])
        outstanding_lost = lead_obj.search_count([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', False), ('probability', '<=', 0)])

        request.env.cr.execute("""
            SELECT COALESCE(sum(l.expected_revenue), 0.0)
            from crm_lead l
            inner join crm_stage s on s.id = l.stage_id
            where l.user_id in %s and l.company_id in %s and l.type = 'opportunity' and l.active = True and s.name = 'Prospect'
        """, (users_ids, companies_ids or (2, 3),))
        prospect_revenue = '$'+'{:,.2f}'.format(request.env.cr.fetchone()[0])

        request.env.cr.execute("""
            SELECT COALESCE(sum(l.expected_revenue), 0.0)
            from crm_lead l
            inner join crm_stage s on s.id = l.stage_id
            where l.user_id in %s and l.company_id in %s and l.type = 'opportunity' and l.active = True and s.name = 'Opportunity'
        """, (users_ids, companies_ids or (2, 3),))
        opportunity_revenue = '$'+'{:,.2f}'.format(request.env.cr.fetchone()[0])

        request.env.cr.execute("""
            SELECT COALESCE(sum(l.expected_revenue), 0.0)
            from crm_lead l
            inner join crm_stage s on s.id = l.stage_id
            where l.user_id in %s and l.company_id in %s and l.type = 'opportunity' and l.active = True and s.name = 'Report'
        """, (users_ids, companies_ids or (2, 3),))
        report_revenue = '$'+'{:,.2f}'.format(request.env.cr.fetchone()[0])

        request.env.cr.execute("""
            SELECT COALESCE(sum(l.expected_revenue), 0.0)
            from crm_lead l
            inner join crm_stage s on s.id = l.stage_id
            where l.user_id in %s and l.company_id in %s and l.type = 'opportunity' and l.active = True and s.name = 'Pending'
        """, (users_ids, companies_ids or (2, 3),))
        pending_revenue = '$'+'{:,.2f}'.format(request.env.cr.fetchone()[0])

        request.env.cr.execute("""
            SELECT 
                CASE WHEN l.active = True then s.name else 'Lost' END as new_name,
                count(l.id) as total,
                cast(sum(l.expected_revenue) as money) as amount
            from crm_lead l
            inner join crm_stage s on s.id = l.stage_id
            where l.user_id in %s and l.company_id in %s and l.type = 'opportunity'
            and s.name in ('Opportunity', 'Report', 'Pending', 'Won', 'Lost')
            group by l.active, new_name, s.id
            order by l.active desc, s.sequence
            limit 5
        """, (users_ids, companies_ids or (2, 3),))
        funnel_data = request.env.cr.dictfetchall()
        count = 0

        fname1 = ''
        fcount1 = 0
        fmoun1 = '$0.00'
        fname2 = ''
        fcount2 = 0
        fmoun2 = '$0.00'
        fname3 = ''
        fcount3 = 0
        fmoun3 = '$0.00'
        fname4 = ''
        fcount4 = 0
        fmoun4 = '$0.00'
        fname5 = ''
        fcount5 = 0
        fmoun5 = '$0.00'
        for funnel in funnel_data:
            count += 1
            if funnel['new_name'] == 'Opportunity':
                fname1 = funnel['new_name']
                fcount1 = funnel['total']
                fmoun1 = funnel['amount']
            elif funnel['new_name'] == 'Report':
                fname2 = funnel['new_name']
                fcount2 = funnel['total']
                fmoun2 = funnel['amount']
            elif funnel['new_name'] == 'Pending':
                fname3 = funnel['new_name']
                fcount3 = funnel['total']
                fmoun3 = funnel['amount']
            elif funnel['new_name'] == 'Won':
                fname4 = funnel['new_name']
                fcount4 = funnel['total']
                fmoun4 = funnel['amount']
            elif funnel['new_name'] == 'Lost':
                fname5 = funnel['new_name']
                fcount5 = funnel['total']
                fmoun5 = funnel['amount']

        results = {
            'active_lead': active_lead,
            'active_lead_l7': active_lead_l7,
            'active_lead_g7': active_lead_g7,
            'lead_lost': lead_lost,

            'active_prospect': active_prospect,
            'active_opportunity': active_opportunity,
            'active_report': active_report,
            'active_pending': active_pending,
            'opportunity_revenue': opportunity_revenue,
            'prospect_revenue': prospect_revenue,
            'report_revenue': report_revenue,
            'pending_revenue': pending_revenue,
            'outstanding_won': outstanding_won,
            'outstanding_lost': outstanding_lost,
            'funnel_data': funnel_data,

            'fname1': fname1,
            'fcount1': fcount1,
            'fmoun1': fmoun1,
            'fname2': fname2,
            'fcount2': fcount2,
            'fmoun2': fmoun2,
            'fname3': fname3,
            'fcount3': fcount3,
            'fmoun3': fmoun3,
            'fname4': fname4,
            'fcount4': fcount4,
            'fmoun4': fmoun4,
            'fname5': fname5,
            'fcount5': fcount5,
            'fmoun5': fmoun5,
        }
        return results

class ChartData(http.Controller):

    @http.route('/odes_custom/fetch_chart_data', type="http", auth='user', crsf=False)
    def fetch_chart_data(self, **post):
        user = request.env.user
        users_ids_search = False
        if not post.get('user') or post.get('user') == 'false':
            if user._is_manager():
                request.env.cr.execute("""
                    SELECT ru.id
                    from res_users ru
                    where ru.active = True and ru.share = False
                """)
                users_res = request.env.cr.fetchall()
                users_ids = tuple([x[0] for x in users_res])
                users_ids_search = users_ids
                users_ids_search += False,
            else:
                users_ids = tuple([user.id])
        else:
            users_ids = tuple([int(post['user'])])
        if not users_ids_search:
            users_ids_search = users_ids

        if not post.get('company') or post.get('company') == 'false':
            # companies_ids = tuple(user.company_ids.ids)
            companies_ids = []
            for comp in user.company_ids:
                if not comp.is_odes:
                    companies_ids.append(comp.id)
            companies_ids = tuple(companies_ids)
        else:
            companies_ids = tuple([int(post['company'])])

        lead_obj = request.env['crm.lead']

        posssibility_leads = lead_obj.search([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'lead'), ('active', '=', True)], order='possibility desc', limit=5)
        lead_label = []#['Red', 'Blue', 'Yellow', 'Green', 'Purple'];
        lead_data = []#[10, 2, 10, 2, 10];
        for lead in posssibility_leads:
            lead_label.append(lead.name)
            lead_data.append(lead.possibility)

        posssibility_opps = lead_obj.search([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.is_won', '=', False)], order='possibility desc', limit=5)
        opp_label = []#['Red', 'Blue', 'Yellow', 'Green', 'Purple'];
        opp_data = []#[7, 2, 4, 2, 10];
        for opp in posssibility_opps:
            opp_label.append(opp.name)
            opp_data.append(opp.possibility)

        revenue_opps = lead_obj.search([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.is_won', '=', False)], order='expected_revenue desc', limit=5)
        revenue_label = []#['Red', 'Blue', 'Yellow', 'Green', 'Purple'];
        revenue_data = []#[7, 2, 4, 2, 10];
        for revenue in revenue_opps:
            revenue_label.append(revenue.name)
            revenue_data.append(revenue.expected_revenue)

        request.env.cr.execute("""
            SELECT 
                CASE WHEN l.active = True then s.name else 'Lost' END as new_name,
                sum(l.expected_revenue)
            from crm_lead l
            inner join crm_stage s on s.id = l.stage_id
            where l.user_id in %s and l.company_id in %s and l.type = 'opportunity'
            group by l.active, new_name
            order by count(l.id) desc
            limit 7
        """, (users_ids, companies_ids or (2, 3),))
        funnel_data = request.env.cr.fetchall()#['Qualified', 7], ['Proposition', 10], ['Won', 10], ['Lost', 10]

        request.env.cr.execute("""
            SELECT 
                CASE WHEN l.active = True then s.name else 'Lost' END as new_name,
                count(l.id)
            from crm_lead l
            inner join crm_stage s on s.id = l.stage_id
            where l.user_id in %s and l.company_id in %s and l.type = 'opportunity'
            group by l.active, new_name, s.sequence
            order by l.active desc, s.sequence
        """, (users_ids, companies_ids or (2, 3),))
        result = request.env.cr.fetchall()
        crm_label = []
        crm_data = []
        for res1 in result:
            crm_label.append(res1[0])
            crm_data.append(res1[1])
        
        results = {
            'lead_label':lead_label,
            'lead_data':lead_data,
            'opp_label':opp_label,
            'opp_data':opp_data,
            'revenue_label':revenue_label,
            'revenue_data':revenue_data,
            'funnel_data':funnel_data,

            # NEWLY ADDED
            'crm_label':crm_label,
            'crm_data':crm_data,
        }

        return json.dumps(results)

    @http.route('/odes_custom/fetch_user_data', type="http", auth='user', crsf=False)
    def fetch_user_data(self):
        user = request.env.user
        is_manager = user._is_manager()

        user_data = []
        if is_manager:
            user_data.append({"text": 'All', "value": False})
            request.env.cr.execute("""
                SELECT rp.name, ru.id
                from res_users ru
                inner join res_partner rp on rp.id = ru.partner_id
                where ru.active = True and ru.share = False
                order by rp.name;
            """)
            users_list = request.env.cr.fetchall()
            for users in users_list:
                user_data.append({"text": users[0], "value": users[1]})
        else:
            user_data.append({"text": user.partner_id.name, "value": user.id})

        company_data = [{"text": 'All', "value": False}]
        for company in user.company_ids:
            if not company.is_odes:
                company_data.append({"text": company.name, "value": company.id})

        user_results = {
            'user_data':  user_data,
            'company_data':  company_data
        }

        return json.dumps(user_results)


    @http.route('/odes_custom/fetch_chart_data_second', type="http", auth='user', crsf=False)
    def fetch_chart_data_second(self, **post):

        user = request.env.user
        request.env.cr.execute("""
            SELECT ru.id
            from res_users ru
            where ru.active = True and ru.share = False
        """)
        users_res = request.env.cr.fetchall()
        users_ids = tuple([x[0] for x in users_res])
        users_ids_search = users_ids
        users_ids_search += False,

        companies_ids = []
        for comp in user.company_ids:
            if comp.is_odes:
                companies_ids.append(comp.id)
        companies_ids = tuple(companies_ids)

        lead_obj = request.env['crm.lead']
        lead_opps = lead_obj.search([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.name', '=', 'Opportunity')], order='expected_revenue desc', limit=5)
        lead_second_label = []#['Red', 'Blue', 'Yellow', 'Green', 'Purple'];
        lead_second_data = []#[7, 2, 4, 2, 10];
        for lead in lead_opps:
            lead_second_label.append(lead.name)
            lead_second_data.append(lead.expected_revenue)

        pending_opps = lead_obj.search([('user_id', 'in', users_ids_search), ('company_id', 'in', companies_ids), ('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.name', '=', 'Pending')], order='expected_revenue desc', limit=5)
        pending_label = []#['Red', 'Blue', 'Yellow', 'Green', 'Purple'];
        pending_data = []#[7, 2, 4, 2, 10];
        for pending in pending_opps:
            pending_label.append(pending.name)
            pending_data.append(pending.expected_revenue)
        
        results = {
            'lead_second_label':lead_second_label,
            'lead_second_data':lead_second_data,
            'pending_label':pending_label,
            'pending_data':pending_data,
        }

        return json.dumps(results)