import base64
import random
import secrets

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SignRequest(models.Model):
    _name = 'sign.request'
    _description = 'Sign Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    template_id = fields.Many2one('sign.template', required=True, tracking=True)
    access_token = fields.Char(default=lambda self: secrets.token_urlsafe(24), copy=False)
    state = fields.Selection(
        [('draft', 'Draft'), ('sent', 'Sent'), ('signed', 'Signed'), ('cancel', 'Cancelled')],
        default='draft',
        tracking=True,
    )
    request_item_ids = fields.One2many('sign.request.item', 'request_id')
    log_ids = fields.One2many('sign.log', 'request_id')
    completion_date = fields.Datetime(readonly=True)
    signed_attachment_id = fields.Many2one('ir.attachment', readonly=True)

    def action_send(self):
        for request in self:
            if not request.request_item_ids:
                raise UserError(_('Please add at least one signer.'))
            request.request_item_ids.filtered(lambda i: i.state == 'draft').write({'state': 'sent'})
            request.request_item_ids.filtered(lambda i: i.state == 'sent').action_send_otp()
            request.state = 'sent'
            request._log_event('sent', _('Request sent to signers.'))
        return True

    def _check_completion(self):
        for request in self:
            items = request.request_item_ids
            if items and all(item.state == 'signed' for item in items):
                request.write({'state': 'signed', 'completion_date': fields.Datetime.now()})
                request._log_event('signed', _('All signers have completed the request.'))

    def action_cancel(self):
        self.write({'state': 'cancel'})
        for request in self:
            request._log_event('cancel', _('Request cancelled.'))
        return True

    def _log_event(self, action, details='', item=False, ip_address=False, user_agent=False):
        self.ensure_one()
        self.env['sign.log'].sudo().create({
            'request_id': self.id,
            'item_id': item.id if item else False,
            'action': action,
            'details': details or '',
            'ip_address': ip_address or '',
            'user_agent': user_agent or '',
        })


class SignRequestItem(models.Model):
    _name = 'sign.request.item'
    _description = 'Sign Request Item'

    request_id = fields.Many2one('sign.request', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', required=True)
    role = fields.Char(default='Signer')
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent'), ('signed', 'Signed')], default='draft')
    signed_on = fields.Datetime(readonly=True)
    signature = fields.Binary(attachment=True)
    signature_text = fields.Char()
    otp_code = fields.Char(readonly=True, copy=False)
    otp_expires_at = fields.Datetime(readonly=True, copy=False)
    otp_attempt_count = fields.Integer(default=0)
    otp_input = fields.Char(string='OTP')
    signed_ip = fields.Char(readonly=True)
    signed_user_agent = fields.Char(readonly=True)

    def action_send_otp(self):
        for item in self:
            otp = '%06d' % random.randint(0, 999999)
            item.write({
                'otp_code': otp,
                'otp_expires_at': fields.Datetime.add(fields.Datetime.now(), minutes=10),
                'otp_attempt_count': 0,
            })
            item.request_id._log_event(
                'otp_sent',
                _('OTP generated for signer: %s') % item.partner_id.display_name,
                item=item,
            )
        return True

    def _validate_otp(self):
        self.ensure_one()
        if not self.otp_code:
            raise UserError(_('OTP is not generated yet. Use "Send OTP" first.'))
        if not self.otp_input:
            raise UserError(_('OTP is required.'))
        if self.otp_expires_at and fields.Datetime.now() > self.otp_expires_at:
            raise UserError(_('OTP expired. Generate a new OTP and try again.'))
        if self.otp_input != self.otp_code:
            self.otp_attempt_count += 1
            raise UserError(_('Invalid OTP code.'))

    def action_sign_now(self):
        for item in self:
            if item.state not in ('sent', 'draft'):
                continue
            if not item.signature and item.signature_text:
                item.signature = base64.b64encode(item.signature_text.encode('utf-8'))
            if not item.signature:
                raise UserError(_('Please provide a signature first.'))
            item._validate_otp()
            ctx = self.env.context
            item.write({
                'state': 'signed',
                'signed_on': fields.Datetime.now(),
                'signed_ip': ctx.get('signed_ip', ''),
                'signed_user_agent': ctx.get('signed_user_agent', ''),
            })
            item.request_id._log_event(
                'sign',
                _('Signer completed signature: %s') % item.partner_id.display_name,
                item=item,
                ip_address=item.signed_ip,
                user_agent=item.signed_user_agent,
            )
            item.request_id._check_completion()
        return True
