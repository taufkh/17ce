from odoo import fields, models


class SignLog(models.Model):
    _name = 'sign.log'
    _description = 'Sign Log'
    _order = 'create_date desc, id desc'

    request_id = fields.Many2one('sign.request', required=True, ondelete='cascade')
    item_id = fields.Many2one('sign.request.item', ondelete='set null')
    action = fields.Selection(
        [('sent', 'Sent'), ('otp_sent', 'OTP Sent'), ('sign', 'Signed'), ('signed', 'Completed'), ('cancel', 'Cancelled')],
        required=True,
    )
    details = fields.Text()
    ip_address = fields.Char()
    user_agent = fields.Char()

