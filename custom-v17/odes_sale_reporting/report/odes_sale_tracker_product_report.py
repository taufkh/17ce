# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class OdesSaleTrackerProductReport(models.Model):
    _name = "odes.sale.tracker.product.report"
    _description = "Sales Tracker Product Report"
    _auto = False
    _rec_name = 'product_id'
    _order = 'product_id desc'

    date = fields.Date('SO Date', readonly=True)
    product_brand_id = fields.Many2one('product.brand', 'Brand', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    so_number = fields.Char('SO Number', readonly=True)
    total_sales = fields.Float('Total S.P', readonly=True)
    total_cost = fields.Float('Total C.P', readonly=True)
    gross_profit = fields.Float('Gross Profit', readonly=True)

    origin_sol_currency_id = fields.Many2one('res.currency', 'Origin Currency(S.P)', readonly=True)
    origin_pol_currency_id = fields.Many2one('res.currency', 'Origin Currency(C.P)', readonly=True)
    sol_currency_rate = fields.Float('Currency rate to USD (S.P)', digits=0, readonly=True)
    pol_currency_rate = fields.Float('Currency rate to USD (C.P)', digits=0, readonly=True)

    origin_total_sales = fields.Float('Origin Total S.P', readonly=True)
    origin_total_cost = fields.Float('Origin Total C.P', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Sales Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True)



    def search(self, args, **kwargs):
        allowed_company_ids = self.env.context.get('allowed_company_ids')
        if allowed_company_ids:
            args += [('company_id','in',allowed_company_ids)]

        return super(OdesSaleTrackerProductReport, self).search(args, **kwargs)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        allowed_company_ids = self.env.context.get('allowed_company_ids')
        if allowed_company_ids:
            domain += [('company_id','in',allowed_company_ids)]

        res = super(OdesSaleTrackerProductReport, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res
        

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        _select_total_sales = """
            (
                CASE
                    WHEN sol.currency_id NOT IN (SELECT rc2.id FROM res_currency rc2 WHERE rc2.name = 'USD')  
                    THEN
                        (SELECT (sol.price_subtotal / t_rate.rate)
                         FROM (
                            SELECT c.id,
                            COALESCE((SELECT r.rate FROM res_currency_rate r
                                WHERE r.currency_id = c.id AND r.name <= so.date_order 
                                    AND (r.company_id IS NULL OR r.company_id = sol.company_id)
                                ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) AS rate
                            FROM res_currency c
                            WHERE c.id IN (sol.currency_id)
                            ) AS t_rate
                         LIMIT 1)
                    ELSE 
                        (sol.price_subtotal)
                END 
            )
            """
        _select_total_cost = """
            ( 
                CASE
                    WHEN pol.currency_id NOT IN (SELECT rc2.id FROM res_currency rc2 WHERE rc2.name = 'USD')   
                    THEN
                        (SELECT ((pol.price_unit * sol.product_uom_qty) / t_rate.rate)
                         FROM (
                            SELECT c.id,
                            COALESCE((SELECT r.rate FROM res_currency_rate r
                                WHERE r.currency_id = c.id AND r.name <= so.date_order 
                                    AND (r.company_id IS NULL OR r.company_id = pol.company_id)
                                ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) AS rate
                            FROM res_currency c
                            WHERE c.id IN (pol.currency_id)
                            ) AS t_rate
                         LIMIT 1)
                    ELSE 
                        (pol.price_unit * sol.product_uom_qty)
                END 
            )
            """

        ## Gross Profit = Total S.P - Total C.P
        _select_gross_profit = """
            (
                (
                    CASE
                        WHEN sol.currency_id NOT IN (SELECT rc2.id FROM res_currency rc2 WHERE rc2.name = 'USD')   
                        THEN
                            (SELECT (sol.price_subtotal / t_rate.rate)
                             FROM (
                                SELECT c.id,
                                COALESCE((SELECT r.rate FROM res_currency_rate r
                                    WHERE r.currency_id = c.id AND r.name <= so.date_order 
                                        AND (r.company_id IS NULL OR r.company_id = sol.company_id)
                                    ORDER BY r.company_id, r.name DESC
                                      LIMIT 1), 1.0) AS rate
                                FROM res_currency c
                                WHERE c.id IN (sol.currency_id)
                                ) AS t_rate
                             LIMIT 1)
                        ELSE 
                            (sol.price_subtotal)
                    END 
                )
                -
                ( 
                    CASE
                        WHEN pol.currency_id NOT IN (SELECT rc2.id FROM res_currency rc2 WHERE rc2.name = 'USD')  
                        THEN
                            (SELECT ((pol.price_unit * sol.product_uom_qty) / t_rate.rate)
                             FROM (
                                SELECT c.id,
                                COALESCE((SELECT r.rate FROM res_currency_rate r
                                    WHERE r.currency_id = c.id AND r.name <= so.date_order 
                                        AND (r.company_id IS NULL OR r.company_id = pol.company_id)
                                    ORDER BY r.company_id, r.name DESC
                                      LIMIT 1), 1.0) AS rate
                                FROM res_currency c
                                WHERE c.id IN (pol.currency_id)
                                ) AS t_rate
                             LIMIT 1)
                        ELSE 
                            (pol.price_unit * sol.product_uom_qty)
                    END 
                )
            )
            """

        _select_sol_currency_rate = """
         (
                CASE
                    WHEN sol.currency_id NOT IN (SELECT rc2.id FROM res_currency rc2 WHERE rc2.name = 'USD')  
                    THEN
                        (SELECT (t_rate.rate)
                         FROM (
                            SELECT c.id,
                            COALESCE((SELECT r.rate FROM res_currency_rate r
                                WHERE r.currency_id = c.id AND r.name <= so.date_order 
                                    AND (r.company_id IS NULL OR r.company_id = sol.company_id)
                                ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) AS rate
                            FROM res_currency c
                            WHERE c.id IN (sol.currency_id)
                            ) AS t_rate
                         LIMIT 1)
                    ELSE 
                        (1)
                END 
            )
            """
        _select_pol_currency_rate = """
            ( 
                CASE
                    WHEN pol.currency_id NOT IN (SELECT rc2.id FROM res_currency rc2 WHERE rc2.name = 'USD')   
                    THEN
                        (SELECT (t_rate.rate)
                         FROM (
                            SELECT c.id,
                            COALESCE((SELECT r.rate FROM res_currency_rate r
                                WHERE r.currency_id = c.id AND r.name <= so.date_order 
                                    AND (r.company_id IS NULL OR r.company_id = pol.company_id)
                                ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) AS rate
                            FROM res_currency c
                            WHERE c.id IN (pol.currency_id)
                            ) AS t_rate
                         LIMIT 1)
                    ELSE 
                        (1)
                END 
            )
            """

        select_ = """
            sol.id AS id,
            so.date_order AS date,
            pt.product_brand_id AS product_brand_id,
            sol.product_id, 
            sol.company_id AS company_id,

            so.name AS so_number,
            so.state AS state,

            sol.currency_id AS origin_sol_currency_id,
            pol.currency_id AS origin_pol_currency_id,
            {sol_currency_rate} AS sol_currency_rate,
            {pol_currency_rate} AS pol_currency_rate,

            sol.price_subtotal AS origin_total_sales, -- Total S.P Unconverted Price
            (pol.price_unit * sol.product_uom_qty) AS origin_total_cost, --Total C.P Unconverted Price

            {total_sales} AS total_sales, -- Total S.P COnverted to USD
            {total_cost} AS total_cost, --Total C.P COnverted to USD
            {gross_profit} AS gross_profit --Gross Profit COnverted to USD
        """.format(
            total_sales=_select_total_sales,
            total_cost=_select_total_cost,
            gross_profit=_select_gross_profit,
            sol_currency_rate=_select_sol_currency_rate,
            pol_currency_rate=_select_pol_currency_rate,
            )

        for field in fields.values():
            select_ += field

        from_ = """
            sale_order_line AS sol
                JOIN sale_order AS so
                    ON (so.id = sol.order_id)
                JOIN product_product AS pp
                    ON (pp.id = sol.product_id )
                JOIN product_template AS pt
                    ON (pt.id = pp.product_tmpl_id) 
                JOIN purchase_order_line AS pol
                    ON (pol.id = sol.purchase_order_line_id) 
                %s
        """ % from_clause

        groupby_ = """
            sol.id,

            sol.company_id,
            pol.company_id,
            sol.currency_id,
            pol.currency_id, 
            
            so.name,
            so.state,
            so.date_order,

            pt.product_brand_id,
            sol.product_id,
            sol.price_subtotal,

            pol.price_unit

             %s
        """ % (groupby)

        query = '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, select_, from_, groupby_)
        # print("##############################################")
        # print("query:::",query)
        return query



    def init(self):
        # self._table = 'odes_sale_tracker_product_report'
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))