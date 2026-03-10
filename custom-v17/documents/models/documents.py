import io
import secrets
import zipfile

from odoo import fields, models


class DocumentsTag(models.Model):
    _name = 'documents.tag'
    _description = 'Document Tag'

    name = fields.Char(required=True)


class DocumentsFolder(models.Model):
    _name = 'documents.folder'
    _description = 'Document Folder'

    name = fields.Char(required=True)


class DocumentsDocument(models.Model):
    _name = 'documents.document'
    _description = 'Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    url = fields.Char()
    folder_id = fields.Many2one('documents.folder')
    tag_ids = fields.Many2many('documents.tag')
    partner_id = fields.Many2one('res.partner')
    owner_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    lock_uid = fields.Many2one('res.users')
    type = fields.Selection([('binary', 'Binary'), ('url', 'URL'), ('empty', 'Empty')], default='url')
    datas = fields.Binary(attachment=True)
    mimetype = fields.Char(default='application/octet-stream')
    store_fname = fields.Char()


class DocumentsShare(models.Model):
    _name = 'documents.share'
    _description = 'Document Share'

    name = fields.Char(required=True)
    access_token = fields.Char(default=lambda self: secrets.token_urlsafe(24), copy=False)
    date_deadline = fields.Date()
    action = fields.Selection([('download', 'Download'), ('downloadupload', 'Download and Upload')], default='download')
    type = fields.Selection([('ids', 'Selected'), ('domain', 'Domain')], default='ids')
    document_ids = fields.Many2many('documents.document', string='Documents')
    is_expired = fields.Boolean(compute='_compute_is_expired')

    def _compute_is_expired(self):
        today = fields.Date.today()
        for share in self:
            share.is_expired = bool(share.date_deadline and share.date_deadline < today)

    def _is_active_share(self):
        self.ensure_one()
        return not self.is_expired and bool(self.document_ids)

    def _check_token(self, token):
        self.ensure_one()
        return token == self.access_token and self._is_active_share()

    def _get_documents_and_check_access(self, token, operation='read'):
        self.ensure_one()
        if not self._check_token(token):
            return self.env['documents.document']
        return self.document_ids


class DocumentsUploadWizard(models.TransientModel):
    _name = 'documents.upload.url.wizard'
    _description = 'Upload URL Wizard'

    name = fields.Char(required=True)
    url = fields.Char(required=True)
    folder_id = fields.Many2one('documents.folder')
    tag_ids = fields.Many2many('documents.tag')

    def action_add(self):
        self.ensure_one()
        self.env['documents.document'].create({
            'name': self.name,
            'url': self.url,
            'folder_id': self.folder_id.id,
            'tag_ids': [(6, 0, self.tag_ids.ids)],
            'type': 'url',
        })
        return {'type': 'ir.actions.act_window_close'}
