from odoo import fields, models


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    account_move_id = fields.Many2one('account.move', string='Journal Entry')
