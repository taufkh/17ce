# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class OdesYearlyBillingSummaryReport(models.Model):
    _name = "odes.yearly.billing.summary.report"
    _description = "Yearly Billing Summary Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    year = fields.Char('Year', readonly=True)
    date = fields.Date('Date', readonly=True)
    product_brand_id = fields.Many2one('product.brand', 'Brand', readonly=True)
    price_unit = fields.Float('Price', readonly=True)
    price_subtotal = fields.Float('Total', readonly=True) 
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True)

    currency_rate = fields.Float('Currency rate to USD', digits=0, readonly=True)
    origin_currency_id = fields.Many2one('res.currency', 'Origin Currency', readonly=True)
    origin_price_subtotal = fields.Float('Origin Total', readonly=True) 


    def search(self, args, **kwargs):
        allowed_company_ids = self.env.context.get('allowed_company_ids')
        if allowed_company_ids:
            args += [('company_id','in',allowed_company_ids)]
            
        return super(OdesYearlyBillingSummaryReport, self).search(args, **kwargs)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        allowed_company_ids = self.env.context.get('allowed_company_ids')
        if allowed_company_ids:
            domain += [('company_id','in',allowed_company_ids)]

        res = super(OdesYearlyBillingSummaryReport, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res
        
    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        _select_price_subtotal = """
            (
                CASE
                    WHEN aml.currency_id NOT IN (SELECT rc2.id FROM res_currency rc2 WHERE rc2.name = 'USD')  
                    THEN
                        (SELECT (aml.price_subtotal / t_rate.rate)
                         FROM (
                            SELECT c.id,
                            COALESCE((SELECT r.rate FROM res_currency_rate r
                                WHERE r.currency_id = c.id AND r.name <= am.invoice_date 
                                    AND (r.company_id IS NULL OR r.company_id = aml.company_id)
                                ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) AS rate
                            FROM res_currency c
                            WHERE c.id IN (aml.currency_id)
                            ) AS t_rate
                         LIMIT 1)
                    ELSE 
                        (aml.price_subtotal)
                END 
            )
            """

        _select_currency_rate = """
            (
                CASE
                    WHEN aml.currency_id NOT IN (SELECT rc2.id FROM res_currency rc2 WHERE rc2.name = 'USD')  
                    THEN
                        (SELECT (t_rate.rate)
                         FROM (
                            SELECT c.id,
                            COALESCE((SELECT r.rate FROM res_currency_rate r
                                WHERE r.currency_id = c.id AND r.name <= am.invoice_date 
                                    AND (r.company_id IS NULL OR r.company_id = aml.company_id)
                                ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) AS rate
                            FROM res_currency c
                            WHERE c.id IN (aml.currency_id)
                            ) AS t_rate
                         LIMIT 1)
                    ELSE 
                        (1)
                END 
            )
            """

        select_ = """
            aml.id,
            to_char(am.invoice_date,'Mon-YYYY') AS month,
            to_char(am.invoice_date,'YYYY') AS year,
            am.invoice_date AS date,
            pt.product_brand_id AS product_brand_id,
            am.state AS state,
            aml.company_id AS company_id,

            aml.currency_id AS origin_currency_id,
            {currency_rate} AS currency_rate,
            aml.price_subtotal AS origin_price_subtotal,

            aml.price_unit AS price_unit,
            {price_subtotal} AS price_subtotal
        """.format(
            price_subtotal=_select_price_subtotal,
            currency_rate=_select_currency_rate,
            )

        for field in fields.values():
            select_ += field

        from_ = """
                account_move_line AS aml
                    INNER JOIN account_move AS am
                        ON am.id = aml.move_id
                    INNER JOIN product_product AS pp
                        ON pp.id = aml.product_id 
                    INNER JOIN product_template AS pt
                        ON pt.id = pp.product_tmpl_id 
                %s
        """ % from_clause 

        groupby_ = """
            aml.id,
            to_char(am.invoice_date,'Mon-YYYY'), -- month,
            to_char(am.invoice_date,'YYYY'), -- year,
            am.invoice_date,
            pt.product_brand_id,
            am.state,
            aml.company_id,
            aml.price_unit,
            aml.price_subtotal
           %s
        """ % (groupby)

        query =  '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, select_, from_, groupby_)
        # print("##########################################")
        # print("query::::",query)
        return query

    def init(self):
        # self._table = odes_yearly_billing_summary_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
