# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class OdesCrmDoc(models.Model):
    _name = 'odes.crm.doc'
    _description = 'Documentations'

    def action_acknowledge(self):
        self.ensure_one()

        if not self.attachment_ids:
            raise UserError(_('Please upload attachment to acknowledge.'))

        self.write({
            'state': 'acknowledged',
            'date_acknowledge': fields.Datetime.now(),
            'acknowledge_user_id': self.env.user.id
        })

    @api.onchange('title_id')
    def _onchange_title_id(self):
        if self.title_id:
            self.name = self.title_id.name

    @api.onchange('attachment_ids')
    def _onchange_attachment_ids(self):
        if self.attachment_ids:
            self.upload_user_id = self.env.user.id
        else:
            self.upload_user_id = False

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence', default=10)
    title_id = fields.Many2one('odes.crm.doc.title', string='Title')
    order_id = fields.Many2one('sale.order', string='Order Reference')
    attachment_ids = fields.Many2many('ir.attachment', 'odes_crm_doc_attachment_ids', 'doc_id', 'attachment_id', string='Attachments')
    upload_user_id = fields.Many2one('res.users', string='Uploaded By')
    date = fields.Datetime('Date', default=fields.Datetime.now())
    date_acknowledge = fields.Datetime('Acknowledged Date')
    acknowledge_user_id = fields.Many2one('res.users', string='Acknowledged By')
    state = fields.Selection([('draft', 'Draft'), ('acknowledged', 'Acknowledged')], default='draft', string='Status')