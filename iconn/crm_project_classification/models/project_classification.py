from odoo import api, fields, models


class ProjectCategory(models.Model):
    _name = 'crm.project.category'
    _description = 'Project Category'

    name = fields.Char(required=True)


class ProjectStatus(models.Model):
    _name = 'crm.project.status'
    _description = 'Project Status'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    category_id = fields.Many2one('crm.project.category', string='Category', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    is_closed = fields.Boolean(default=False)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    project_category_id = fields.Many2one(
        'crm.project.category',
        string='Project Category',
    )
    project_status_id = fields.Many2one(
        'crm.project.status',
        string='Project Status',
    )

    @api.onchange('project_category_id')
    def _onchange_project_category(self):
        self.project_status_id = False
