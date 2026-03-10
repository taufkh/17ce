# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class OdesSaleTrackerReport(models.Model):
    _name = "odes.sale.billing.detail.report"
    _description = "Sales Billing Detail"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'


    month = fields.Char('Month', readonly=True)
    ttype = fields.Char('Type', readonly=True)
    date = fields.Date('Date', readonly=True)
    invoice_id = fields.Many2one('account.move', 'Num', readonly=True)
    purchase_order_id = fields.Many2one('purchase.order', 'P.O. No', readonly=True)
    customer_code = fields.Char('Customer Code')
    partner_id = fields.Many2one('res.partner', 'Name', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    country_id = fields.Many2one('res.country', 'Customer Country', readonly=True)
    product_id = fields.Many2one('product.product', 'Item Code', readonly=True)
    item_description = fields.Char('Item Description', readonly=True)
    product_brand_id = fields.Many2one('product.brand', 'Brand', readonly=True)
    qty = fields.Float('Qty', readonly=True)

    sales_price = fields.Float('Sales Price', readonly=True)
    total_sales = fields.Float('Total Sales', readonly=True)
    cost_price = fields.Float('Cost Price', readonly=True)
    total_cost = fields.Float('Total Cost', readonly=True)
    gross_profit = fields.Float('Gross Profit', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)

    
    origin_sales_price = fields.Float('Origin Unit SP', readonly=True)
    origin_total_sales = fields.Float('Origin PO Amount', readonly=True)
    origin_cost_price = fields.Float('Origin MC CP', readonly=True)
    origin_total_cost = fields.Float('Origin Total CP', readonly=True)

    origin_sol_currency_id = fields.Many2one('res.currency', 'Origin Currency(S.P)', readonly=True)
    origin_pol_currency_id = fields.Many2one('res.currency', 'Origin Currency(C.P)', readonly=True)
    sol_currency_rate = fields.Float('Currency rate to USD (S.P)', digits=0, readonly=True)
    pol_currency_rate = fields.Float('Currency rate to USD (C.P)', digits=0, readonly=True)




    def search(self, args, **kwargs):
        allowed_company_ids = self.env.context.get('allowed_company_ids')
        if allowed_company_ids:
            args += [('company_id','in',allowed_company_ids)]
            
        return super(OdesSaleTrackerReport, self).search(args, **kwargs)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        allowed_company_ids = self.env.context.get('allowed_company_ids')
        if allowed_company_ids:
            domain += [('company_id','in',allowed_company_ids)]

        res = super(OdesSaleTrackerReport, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res


    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""


        _select_sales_price = """
            (
                CASE
                    WHEN sol.currency_id NOT IN (SELECT rc2.id FROM res_currency rc2 WHERE rc2.name = 'USD')  
                    THEN
                        (SELECT (sol.price_unit / t_rate.rate)
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
                        (sol.price_unit)
                END 
            )
            """
        _select_cost_price = """
            ( 
                CASE
                    WHEN pol.currency_id NOT IN (SELECT rc2.id FROM res_currency rc2 WHERE rc2.name = 'USD')   
                    THEN
                        (SELECT (pol.price_unit / t_rate.rate)
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
                        (pol.price_unit)
                END 
            )
            """

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
            coalesce(min(aml.id), -am.id) as id, 
            to_char(am.invoice_date,'Mon-YYYY') AS month,
            am.invoice_date AS date,
            'Tax Invoice' AS ttype,
            sol.id AS order_line_id,
           
            sol.purchase_order_line_id AS purchase_order_line_id,

            am.id AS invoice_id,
            po.id AS purchase_order_id, 
            (
                SELECT rp.customer_code from res_partner AS rp
                WHERE rp.id = am.partner_id limit 1
            ) AS customer_code,
            aml.partner_id AS partner_id,
            am.invoice_user_id AS user_id, --sales person
           
            (
                SELECT rc.id from res_country AS rc
                WHERE rc.id = (SELECT rp.country_id from res_partner AS rp
                    WHERE rp.id = am.partner_id limit 1)
                limit 1
            ) AS country_id,

            aml.product_id ,
            aml.name AS item_description,
            pt.product_brand_id AS product_brand_id,
            aml.company_id AS company_id,

            sol.currency_id AS origin_sol_currency_id,
            pol.currency_id AS origin_pol_currency_id,
            {sol_currency_rate} AS sol_currency_rate,
            {pol_currency_rate} AS pol_currency_rate,

            sol.product_uom_qty AS qty,

            sol.price_unit AS origin_sales_price,
            sol.price_subtotal AS origin_total_sales,
            pol.price_unit AS origin_cost_price,
            (pol.price_unit * sol.product_uom_qty) AS origin_total_cost,
            --( sol.price_subtotal - pol.price_subtotal) AS gross_profit

            {sales_price} AS sales_price, --COnverted to USD
            {total_sales} AS total_sales, --COnverted to USD
            {cost_price} AS cost_price, --COnverted to USD
            {total_cost} AS total_cost, --COnverted to USD
            {gross_profit} AS gross_profit --COnverted to USD

        """.format(
            sales_price=_select_sales_price,
            total_sales=_select_total_sales,
            cost_price=_select_cost_price,
            total_cost=_select_total_cost,
            gross_profit=_select_gross_profit, 
            sol_currency_rate=_select_sol_currency_rate,
            pol_currency_rate=_select_pol_currency_rate)

        for field in fields.values():
            select_ += field

        from_ = """
            account_move_line AS aml
                INNER JOIN account_move AS am
                    ON am.id = aml.move_id
                INNER JOIN sale_order_line_invoice_rel AS soli_rel
                    ON soli_rel.invoice_line_id = aml.id
                INNER JOIN sale_order_line AS sol
                    ON sol.id = soli_rel.order_line_id
                INNER JOIN sale_order AS so
                    ON so.id = sol.order_id
                INNER JOIN purchase_order_line AS pol
                    ON pol.id = sol.purchase_order_line_id 
                INNER JOIN purchase_order AS po
                    ON po.id = pol.order_id 
                INNER JOIN product_product AS pp
                    ON pp.id = aml.product_id 
                INNER JOIN product_template AS pt
                    ON pt.id = pp.product_tmpl_id 
                %s
        """ % from_clause 

        groupby_ = """
            to_char(am.invoice_date,'Mon-YYYY'), --month
            am.invoice_date,
            so.date_order,
            sol.id,
            am.id,
            po.id,
            sol.purchase_order_line_id,

            aml.partner_id,
            am.invoice_user_id,

            aml.product_id,
            aml.company_id,

            sol.company_id,
            pol.company_id,
            sol.currency_id,
            pol.currency_id,

            aml.name, -- item_description
            pt.product_brand_id,
            sol.product_uom_qty,
            sol.price_unit,
            sol.price_subtotal,
            pol.price_unit,
            pol.price_subtotal
           %s
        """ % (groupby)

        return '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, select_, from_, groupby_)

    def init(self):
        # self._table = odes_sale_billing_detail_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
