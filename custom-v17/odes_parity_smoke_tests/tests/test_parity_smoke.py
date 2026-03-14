from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestOdesParitySmoke(TransactionCase):
    def test_01_approval_models(self):
        category = self.env['approval.category'].create({'name': 'Smoke CAT', 'is_art_result': True})
        request = self.env['approval.request'].create({
            'name': 'Smoke REQ',
            'category_id': category.id,
            'request_owner_id': self.env.user.id,
        })
        self.assertTrue(category)
        self.assertTrue(request)

    def test_02_appointment_models(self):
        appointment = self.env['calendar.appointment.type'].create({'name': 'Smoke Appointment'})
        self.assertTrue(appointment)
        self.assertTrue(appointment.website_url)

    def test_03_documents_models(self):
        document = self.env['documents.document'].create({
            'name': 'Smoke Doc',
            'url': 'https://example.com',
            'type': 'url',
        })
        share = self.env['documents.share'].create({
            'name': 'Smoke Share',
            'access_token': 'smoke-token',
            'document_ids': [(6, 0, [document.id])],
        })
        available = share._get_documents_and_check_access('smoke-token', operation='read')
        self.assertTrue(document)
        self.assertTrue(share)
        self.assertTrue(available)

    def test_04_social_models(self):
        media = self.env['social.media'].create({'name': 'Facebook'})
        account = self.env['social.account'].create({'name': 'Smoke Account', 'facebook_access_token': 'dummy'})
        post = self.env['social.post'].create({'message': 'https://example.com smoke'})
        live_post = self.env['social.live.post'].create({'account_id': account.id, 'post_id': post.id})
        self.assertTrue(media)
        self.assertTrue(account)
        self.assertTrue(post)
        self.assertTrue(live_post)

    def test_05_design_and_hr_presence(self):
        self.assertIn('odes.rebrand.data', self.env)
        self.assertIn('is_origin_contract_template', self.env['hr.contract']._fields)
