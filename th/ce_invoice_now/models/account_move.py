# -*- coding: utf-8 -*-

import logging

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from ..services import CEInvoiceXMLBuilder

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    ce_client_ref = fields.Char(string='CE Client Ref', copy=False, tracking=True)
    ce_send_invoice_req_status = fields.Char(string='CE Send Invoice Status Code', copy=False, tracking=True)
    ce_send_invoice_content = fields.Text(string='CE Send Invoice Content', copy=False)
    ce_send_invoice_status = fields.Boolean(string='CE Send Invoice Status', copy=False)

    ce_invoice_status_content = fields.Text(string='CE Invoice Status Content', copy=False)
    ce_invoice_status = fields.Char(string='CE Invoice Status Code', copy=False)
    ce_is_completed = fields.Boolean(string='CE Is Completed', copy=False)

    ce_xml_generation_state = fields.Selection(
        [('draft', 'Draft'), ('generated', 'Generated'), ('error', 'Error')],
        string='CE XML Generation State',
        default='draft',
        copy=False,
    )
    ce_xml_attachment_id = fields.Many2one('ir.attachment', string='CE XML Attachment', copy=False)
    ce_xml_error_message = fields.Text(string='CE XML Error Message', copy=False)
    ce_xml_generated_at = fields.Datetime(string='CE XML Generated At', copy=False)
    ce_xml_hash = fields.Char(string='CE XML Hash', copy=False)

    ce_applicable_invoicenow = fields.Boolean(
        string='Applicable for CE InvoiceNow?',
        related='partner_id.ce_applicable_invoicenow',
        store=True,
        readonly=True,
    )

    def _ce_is_supported_doc(self):
        self.ensure_one()
        return self.move_type in ('out_invoice', 'out_refund')

    def _ce_find_existing_xml_attachment(self):
        self.ensure_one()
        if self.ce_xml_attachment_id:
            return self.ce_xml_attachment_id
        return self.attachment_ids.filtered(lambda att: att.name and att.name.endswith('.xml'))[:1]

    def _ce_generate_xml(self, force=False):
        self.ensure_one()
        return CEInvoiceXMLBuilder.generate_or_fail(self, force=force)

    def action_ce_generate_xml(self):
        self.ensure_one()
        if not self._ce_is_supported_doc():
            raise UserError(_('CE XML generation is only available for customer invoice or credit note.'))
        attachment = self._ce_generate_xml(force=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('CE XML Generated'),
                'message': _('Attachment %s has been generated successfully.') % (attachment.name,),
                'sticky': False,
                'type': 'success',
            },
        }

    def action_ce_invoice_now_sent(self):
        self.ensure_one()
        action = self.env.ref('ce_invoice_now.ce_action_send_invoice').read()[0]
        action['context'] = {
            'default_move_type': self.move_type,
            'default_ce_move_id': self.id,
            'active_ids': [self.id],
        }
        return action

    @api.model
    def _check_ce_invoice_status(self):
        config = self.env['ce.invoice.now.configuration'].get_active_configuration()
        if not config:
            return True

        config.action_generate_token()
        if not config.access_token:
            return True

        domain = [
            ('ce_is_completed', '=', False),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', 'not in', ('draft', 'cancel')),
            ('ce_client_ref', '!=', False),
        ]
        invoices = self.search(domain)
        for invoice in invoices:
            url = '%s/business/%s/%s/%s/%s.json' % (
                config.status_uri,
                config.api_version,
                config.inv_document_type,
                config.inv_document_format,
                invoice.ce_client_ref,
            )
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': 'Bearer %s' % config.access_token,
            }
            try:
                response = requests.get(url, headers=headers, timeout=30)
            except requests.RequestException as err:
                _logger.warning('CE InvoiceNow status check failed for invoice %s: %s', invoice.id, err)
                continue

            invoice.ce_invoice_status_content = response.text
            invoice.ce_invoice_status = str(response.status_code)

            if response.status_code != 200:
                continue

            try:
                status_data = response.json()
            except ValueError:
                continue

            if status_data.get('status') == 'Completed':
                invoice.ce_is_completed = True

        return True
