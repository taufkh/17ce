from odoo.tests import common


class TestHrOnboarding(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.job_model = self.env["hr.job"]
        self.employee_model = self.env["hr.employee"]
        self.template_model = self.env["mail.template"]

    def test_job_template_sends_onboarding_email(self):
        template = self.template_model.create(
            {
                "name": "Developer Onboarding",
                "model_id": self.env.ref("hr.model_hr_employee").id,
                "subject": "Welcome Developer",
                "email_from": "hr@example.com",
                "body_html": "<p>Hello</p>",
            }
        )
        job = self.job_model.create(
            {
                "name": "Developer",
                "onboarding_mail_template_id": template.id,
            }
        )
        initial_mail_count = self.env["mail.mail"].search_count([])

        employee = self.employee_model.create(
            {
                "name": "New Developer",
                "job_id": job.id,
                "work_email": "new.developer@example.com",
            }
        )

        self.assertTrue(employee.onboarding_email_sent)
        self.assertEqual(self.env["mail.mail"].search_count([]), initial_mail_count + 1)
        mail = self.env["mail.mail"].search([], order="id desc", limit=1)
        self.assertEqual(mail.email_to, "new.developer@example.com")
