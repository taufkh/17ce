import re
from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError


class SocialMedia(models.Model):
    _name = 'social.media'
    _description = 'Social Media'

    _FACEBOOK_ENDPOINT = 'https://graph.facebook.com'

    name = fields.Char(required=True)
    media_type = fields.Selection([('facebook', 'Facebook')], default='facebook', required=True)


class SocialAccount(models.Model):
    _name = 'social.account'
    _description = 'Social Account'

    name = fields.Char(required=True)
    media_id = fields.Many2one('social.media', required=True)
    page_id = fields.Char()
    facebook_access_token = fields.Char()
    active = fields.Boolean(default=True)


class SocialPostImage(models.Model):
    _name = 'social.post.image'
    _description = 'Social Post Image'

    post_id = fields.Many2one('social.post', required=True, ondelete='cascade')
    store_fname = fields.Char()
    mimetype = fields.Char(default='image/png')

    def _full_path(self, fname):
        return ''


class SocialPost(models.Model):
    _name = 'social.post'
    _description = 'Social Post'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, default='New Social Post')
    message = fields.Text(tracking=True)
    image_ids = fields.One2many('social.post.image', 'post_id')
    state = fields.Selection(
        [('draft', 'Draft'), ('queued', 'Queued'), ('posted', 'Posted'), ('failed', 'Failed')],
        default='draft',
        tracking=True,
    )
    live_post_ids = fields.One2many('social.live.post', 'post_id')

    def _extract_url_from_message(self, message):
        if not message:
            return False
        match = re.search(r'https?://\S+', message)
        return match.group(0) if match else False

    def _format_images_facebook(self, facebook_target_id, access_token):
        return []

    def action_queue(self):
        self.write({'state': 'queued'})
        return True

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
        return True


class SocialLivePost(models.Model):
    _name = 'social.live.post'
    _description = 'Social Live Post'
    _inherit = ['mail.thread']

    account_id = fields.Many2one('social.account', required=True)
    post_id = fields.Many2one('social.post', required=True)
    facebook_post_id = fields.Char()
    posted_on = fields.Datetime(readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('failed', 'Failed')], default='draft')
    failure_reason = fields.Text()

    def action_publish(self):
        for live_post in self:
            account = live_post.account_id
            if not account.facebook_access_token:
                live_post.write({
                    'state': 'failed',
                    'failure_reason': _('Missing Facebook access token.'),
                })
                live_post.post_id.write({'state': 'failed'})
                continue
            if hasattr(live_post, '_post_facebook'):
                # Hook for odes_social_facebook_modifier real publisher.
                target_id = account.page_id or 'me'
                live_post._post_facebook(target_id)
                if live_post.state == 'posted':
                    live_post.write({'posted_on': fields.Datetime.now()})
                    live_post.post_id.write({'state': 'posted'})
                else:
                    live_post.post_id.write({'state': 'failed'})
                continue

            live_post.write({
                'facebook_post_id': f"SIM-{live_post.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                'state': 'posted',
                'failure_reason': False,
                'posted_on': fields.Datetime.now(),
            })
            live_post.post_id.write({'state': 'posted'})
        return True

    def action_retry(self):
        self.write({'state': 'draft', 'failure_reason': False})
        return self.action_publish()
