from odoo import fields, models


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    documents_hr_contract_model = fields.Char(string='Linked Model')
    documents_hr_contract_res_id = fields.Integer(string='Linked Record ID')
