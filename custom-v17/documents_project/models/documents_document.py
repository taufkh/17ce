from odoo import fields, models


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    project_id = fields.Many2one('project.project', string='Project')
    task_id = fields.Many2one('project.task', string='Task')
