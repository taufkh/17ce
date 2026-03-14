from odoo import api, fields, models


class AccountAsset(models.Model):
    _name = 'account.asset'
    _description = 'Fixed Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'acquisition_date desc, id desc'

    name = fields.Char(required=True, tracking=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, readonly=True)
    acquisition_date = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    original_value = fields.Monetary(currency_field='currency_id', required=True, default=0.0, tracking=True)
    book_value = fields.Monetary(currency_field='currency_id', compute='_compute_book_value', store=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('running', 'Running'), ('close', 'Closed')],
        default='draft',
        required=True,
        tracking=True,
    )
    location = fields.Char()
    asset_register_no = fields.Char()

    @api.depends('original_value')
    def _compute_book_value(self):
        for asset in self:
            asset.book_value = asset.original_value

