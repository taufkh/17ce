
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HrYear(models.Model):
    _name = "hr.year"
    _description = "HR Fiscal Year"
    _order = "date_start, id"

    name = fields.Char('HR Year', required=True, help="Name of HR year")
    code = fields.Char('Code', required=True)
    date_start = fields.Date('Start Date', required=True)
    date_stop = fields.Date('End Date', required=True)
    period_ids = fields.One2many('hr.period', 'hr_year_id', 'Periods')
    state = fields.Selection([('draft', 'Draft'),
                              ('open', 'Open'),
                              ('done', 'Closed')], 'Status',
                             default='draft', readonly=True, copy=False)

    _sql_constraints = [
        ('hr_year_code_uniq', 'unique(code)', 'Code must be unique per year!'),
        ('hr_year_name_uniq', 'unique(name)', 'Name must be unique')
    ]

    def close_period(self):
        return self.write({'state': 'done'})

    def create_period(self):
        interval = 1
        for fy in self:
            date_start = fy.date_start
            date_stop = fy.date_stop
            while date_start.strftime('%Y-%m-%d') < \
                    date_stop.strftime('%Y-%m-%d'):
                date_interval = date_start + relativedelta(
                    months=interval, days=-1)
                if date_interval.strftime('%Y-%m-%d') > date_stop.strftime(
                        '%Y-%m-%d'):
                    date_interval = datetime.strptime(fy.date_stop, '%Y-%m-%d')
                self.env['hr.period'].create({
                    'name': date_start.strftime('%m/%Y'),
                    'code': date_start.strftime('%m/%Y'),
                    'date_start': date_start.strftime(
                        '%Y-%m-%d'),
                    'date_stop': date_interval.strftime(
                        '%Y-%m-%d'),
                    'hr_year_id': fy.id,
                })
                date_start = date_start + relativedelta(months=interval)
            fy.write({'state': 'open'})
        return True

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
#         domain = ['|', ('code', operator, name), ('name', operator, name)]
        hr_year_rec = self.search(['|', ('code', operator, name),
                                   ('name', operator, name)] + args,
                                  limit=limit)
        return hr_year_rec.name_get()


class HrPeriod(models.Model):
    _inherit = "hr.period"
    _description = "HR period"
    _order = "date_start desc"

    code = fields.Char('Code')
    special = fields.Boolean('Opening/Closing Period',
                             help="These periods can overlap.")
    hr_year_id = fields.Many2one('hr.year', 'HR Year')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
#         domain = ['|', ('code', operator, name), ('name', operator, name)]
        hr_period_rec = self.search(['|', ('code', operator, name),
                                     ('name', operator, name)] + args,
                                    limit=limit)
        return hr_period_rec.name_get()
