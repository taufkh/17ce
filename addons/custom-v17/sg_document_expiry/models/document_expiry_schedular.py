from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models


class EmployeeImmigration(models.Model):
    _inherit = 'employee.immigration'

    @api.model
    def get_expiry_documents(self):
        """
        This method called when scheduler called and send the mail if any
        document which will expire on next month.
        """
        immigration_obj = self.env['employee.immigration']
        next_date = datetime.today().date() + relativedelta(months=1)
        immigration_rec = immigration_obj.search([
            ('exp_date', '=', next_date)])
        if not immigration_rec:
            return False
        user_rec = self.env['res.users'].search([])
        user_hr_id = user_rec.filtered(
            lambda x: x.has_group('hr.group_hr_manager'
                                  ) or x.has_group('base.group_system'))
        list_mail_ids = [user.login for user in user_hr_id if user.login]
        email_to = ",".join(list_mail_ids)
        template_name = 'sg_document_expiry.email_temp_document_expire'
        template_id = self.env.ref(template_name, raise_if_not_found=False)
        if not template_id:
            return False
        template_id.write({'email_to': email_to})
        # Use a real target record for cron model-level execution.
        template_id.send_mail(immigration_rec[0].id, force_send=True)
        return True
