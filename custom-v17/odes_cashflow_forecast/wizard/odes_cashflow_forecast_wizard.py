from odoo import models, fields, api

class OdesCashflowForecastWizard(models.TransientModel):
    """ Student Migration Wizard """
    _name = "odes.cashflow.forecast.wizard"
    _description = "Wizard for Cashflow Report"

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    date = fields.Date(string="Start Date", default=fields.Date.context_today)