from odoo import fields, models


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    business_grouping_id = fields.Many2one(
        'res.business.grouping',
        string='Business Grouping',
    )
