from odoo import fields, models


class SignTemplate(models.Model):
    _name = 'sign.template'
    _description = 'Sign Template'
    _inherit = ['mail.thread']

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    attachment_id = fields.Many2one('ir.attachment', required=True)
    responsible_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    request_ids = fields.One2many('sign.request', 'template_id')
    field_ids = fields.One2many('sign.template.field', 'template_id', string='Sign Fields')


class SignTemplateField(models.Model):
    _name = 'sign.template.field'
    _description = 'Sign Template Field'
    _order = 'page, y, x, id'

    template_id = fields.Many2one('sign.template', required=True, ondelete='cascade')
    name = fields.Char(required=True)
    field_type = fields.Selection(
        [('signature', 'Signature'), ('text', 'Text'), ('date', 'Date'), ('checkbox', 'Checkbox')],
        default='signature',
        required=True,
    )
    role = fields.Char(default='Signer')
    required = fields.Boolean(default=True)
    page = fields.Integer(default=1, required=True)
    x = fields.Float(string='X', help='Relative X coordinate in page units.')
    y = fields.Float(string='Y', help='Relative Y coordinate in page units.')
    width = fields.Float(default=120.0)
    height = fields.Float(default=24.0)
