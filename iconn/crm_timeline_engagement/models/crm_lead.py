from odoo import api, fields, models


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'expected_revenue' in fields_list and defaults.get('expected_revenue') is None:
            defaults['expected_revenue'] = 1.0
        return defaults

    x_is_won_stage = fields.Boolean(
        related='stage_id.is_won',
        readonly=True,
    )
    x_is_lost = fields.Boolean(
        compute='_compute_x_is_lost',
        readonly=True,
    )
    x_project_lifespan = fields.Char(
        string='Project Lifespan',
        help='Estimated length of project duration.',
    )
    x_estimated_closing_date = fields.Date(
        string='Estimated Closing Date',
        help='Expected date when this opportunity is likely to close.',
    )
    x_engagement_date = fields.Date(
        string='Engagement Date',
        help='First customer interaction regarding this opportunity.',
    )
    x_sample_quantity = fields.Integer(
        string='Sample Quantity',
        help='Total number of samples sent to client (if applicable).',
    )
    x_possibility = fields.Selection(
        selection=[(str(i), str(i)) for i in range(1, 11)],
        string='Possibility (1-10)',
        help='Likelihood score from 1 (lowest) to 10 (highest).',
    )

    def _compute_x_is_lost(self):
        for lead in self:
            lead.x_is_lost = bool(lead.lost_reason_id)
