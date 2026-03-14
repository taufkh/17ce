from odoo import fields, models


class CrmQuotationManufacturer(models.Model):
    _name = 'crm.quotation.manufacturer'
    _description = 'Manufacturer Master'

    name = fields.Char(string='Manufacturer Name', required=True)


class CrmQuotationLine(models.Model):
    _name = 'crm.quotation.line'
    _description = 'CRM Quotation Line'
    _order = 'id desc'

    select_line = fields.Boolean(string='Select')
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('won', 'Won'),
            ('lost', 'Lost'),
        ],
        string='Status',
        default='draft',
    )
    lead_id = fields.Many2one(
        'crm.lead',
        string='Opportunity',
        required=True,
        ondelete='cascade',
    )
    part_number = fields.Char(string='Part Number')
    product_id = fields.Many2one('product.product', string='Part Number')
    manufacturer_id = fields.Many2one(
        'crm.quotation.manufacturer',
        string='Manufacturer',
    )
    number_of_pr = fields.Integer(string='Number of PR')
    quoted_price = fields.Float(string='Quoted Price')
    competitor_name = fields.Char(string='Competitor Name')
    competitor_mpn = fields.Char(string='Competitor MPN')
    competitor_price = fields.Float(string='Competitor Price')
    competitor_moq = fields.Integer(string='Competitor MOQ')
    note = fields.Text(string='Notes')
    lost_reason_id = fields.Many2one(
        'crm.lost.reason',
        string='Lost Reason',
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Quotation',
    )
