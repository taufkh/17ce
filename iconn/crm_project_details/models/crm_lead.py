from odoo import fields, models


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    project_name = fields.Char(
        string='Project Name',
        related='name',
        store=True,
        readonly=True,
        help='Project name is auto-synced with opportunity title.',
    )
    application_id = fields.Many2one(
        'crm.project.application',
        string='Application',
    )
    end_customer_id = fields.Many2one('res.partner', string='End Customer')
    end_product_id = fields.Many2one('product.product', string='End Product')
    contract_manufacturer = fields.Char(string='Contract Manufacturer')
    design_location = fields.Char(string='Design Location')
    annual_quantity = fields.Integer(string='Annual Quantity')
    mass_production_schedule = fields.Date(string='Mass Production Schedule')
    pilot_run_quantity = fields.Integer(string='Pilot Run Quantity')
    pilot_run_schedule = fields.Date(string='Pilot Run Schedule')
