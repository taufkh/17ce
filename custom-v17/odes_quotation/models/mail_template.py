# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging


from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MailTemplate(models.Model):
    _inherit = ['mail.template']

    def generate_email(self, res_ids, fields):
        """Generates an email from the template for given the given model based on
        records given by res_ids.

        :param res_id: id of the record to use for rendering the template (model
                       is taken from template definition)
        :returns: a dict containing all relevant fields for creating a new
                  mail.mail entry, with one extra key ``attachments``, in the
                  format [(report_name, data)] where data is base64 encoded.
        """
        self.ensure_one()
        multi_mode = True
        if isinstance(res_ids, int):
            res_ids = [res_ids]
            multi_mode = False

        results = dict()
        for lang, (template, template_res_ids) in self._classify_per_lang(res_ids).items():
            for field in fields:
                template = template.with_context(safe=(field == 'subject'))
                generated_field_values = template._render_field(
                    field, template_res_ids,
                    post_process=(field == 'body_html')
                )
                for res_id, field_value in generated_field_values.items():
                    results.setdefault(res_id, dict())[field] = field_value
            # compute recipients
            if any(field in fields for field in ['email_to', 'partner_to', 'email_cc']):
                results = template.generate_recipients(results, template_res_ids)
            # update values for all res_ids
            for res_id in template_res_ids:
                values = results[res_id]
                if values.get('body_html'):
                    values['body'] = tools.html_sanitize(values['body_html'])
                # technical settings
                values.update(
                    mail_server_id=template.mail_server_id.id or False,
                    auto_delete=template.auto_delete,
                    model=template.model,
                    res_id=res_id or False,
                    attachment_ids=[attach.id for attach in template.attachment_ids],
                )

            # Add report in attachments: generate once for all template_res_ids
            if template.report_template:
                for res_id in template_res_ids:
                    attachments = []
                    report_name = self._render_field('report_name', [res_id])[res_id]
                    report = template.report_template
                    report_service = report.report_name

                    if report.report_type in ['qweb-html', 'qweb-pdf']:
                        result, format = report._render_qweb_pdf([res_id])
                    else:
                        res = report._render([res_id])
                        if not res:
                            raise UserError(_('Unsupported report type %s found.', report.report_type))
                        result, format = res

                    # TODO in trunk, change return format to binary to match message_post expected format
                    result = base64.b64encode(result)
                    if not report_name:
                        report_name = 'report.' + report_service
                    ext = "." + format
                    if not report_name.endswith(ext):
                        report_name += ext
                    attachments.append((report_name, result))
                    results[res_id]['attachments'] = attachments

            # IF TEMPLATE IS FOR SALE ORDER. GET THE SALE ORDER COMPANY, THEN GET THE COMPANY SO REPORT PREFERENCE
            if self.model == 'sale.order':

                # SEARCH FOR SALE REPORT
                search_sale_id = self.env['sale.order'].search([('id', '=', res_id)])
                if search_sale_id.company_id.quotation_report_template.name:
                    for res_id in template_res_ids:
                        attachments = []
                        report_name = self._render_field('report_name', [res_id])[res_id]
                        
                        # PUT THE RESULT IN THE REPORT
                        report = search_sale_id.company_id.quotation_report_template
                        report_service = report.report_name

                        if report.report_type in ['qweb-html', 'qweb-pdf']:
                            result, format = report._render_qweb_pdf([res_id])
                        else:
                            res = report._render([res_id])
                            if not res:
                                raise UserError(_('Unsupported report type %s found.', report.report_type))
                            result, format = res

                        # TODO in trunk, change return format to binary to match message_post expected format
                        result = base64.b64encode(result)
                        if not report_name:
                            report_name = 'report.' + report_service
                        ext = "." + format
                        if not report_name.endswith(ext):
                            report_name += ext
                        attachments.append((report_name, result))
                        results[res_id]['attachments'] = attachments

        return multi_mode and results or results[res_ids[0]]