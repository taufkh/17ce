# -*- coding: utf-8 -*-

import logging
import uuid

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CESendInvoiceLine(models.TransientModel):
    _name = 'ce.send.invoice.line'
    _description = 'CE Send Invoice Line'

    attachment_id = fields.Many2one('ir.attachment', string='Attachment')
    move_id = fields.Many2one('account.move', string='Invoice', required=True)
    send_invoice_id = fields.Many2one('ce.send.invoice', required=True)


class CESendInvoice(models.TransientModel):
    _name = 'ce.send.invoice'
    _description = 'CE Send Invoice'

    move_type = fields.Selection(
        [('out_invoice', 'Invoice'), ('out_refund', 'Credit Note')],
        string='Move Type',
        readonly=True,
    )
    ce_move_id = fields.Many2one('account.move', string='Invoice')
    ce_attachment_ids = fields.Many2many('ir.attachment', string='XML Attachments')
    send_invoice_ids = fields.One2many('ce.send.invoice.line', 'send_invoice_id', string='Send Lines')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        move_type = self.env.context.get('default_move_type')
        if move_type not in ('out_invoice', 'out_refund'):
            raise UserError(_('Send to InvoiceNow is only allowed for customer invoice or credit note.'))

        res['move_type'] = move_type

        active_ids = self.env.context.get('active_ids') or []
        moves = self.env['account.move'].browse(active_ids)
        invoice_lines = []
        for move in moves:
            attachment = move._ce_find_existing_xml_attachment()
            invoice_lines.append((0, 0, {'move_id': move.id, 'attachment_id': attachment.id if attachment else False}))

        res['send_invoice_ids'] = invoice_lines
        return res

    def _resolve_xml_attachment(self, invoice, line_attachment, config):
        if line_attachment:
            return line_attachment

        existing = invoice._ce_find_existing_xml_attachment()
        if existing:
            return existing

        if not config.ce_xml_auto_generate:
            raise UserError(
                _('No XML attachment found for invoice %s and auto-generation is disabled.') % (invoice.display_name,)
            )

        return invoice._ce_generate_xml(force=config.ce_xml_force_regenerate)

    def _send_invoice_datapost(self, invoice, attachment, config, document_type, document_format):
        if not invoice.partner_id.ce_applicable_invoicenow:
            return True

        if invoice.ce_send_invoice_status:
            return True

        config.action_generate_token()
        if not config.access_token:
            raise UserError(_('Access token is empty. Please generate token first.'))

        client_ref = uuid.uuid4()
        url = '%s/business/%s/%s/%s/%s' % (
            config.base_uri,
            config.api_version,
            document_type,
            document_format,
            client_ref,
        )
        headers = {'Authorization': 'Bearer %s' % config.access_token}

        if not attachment.store_fname:
            raise UserError(_('Attachment %s has no stored file content.') % (attachment.display_name,))
        file_path = attachment._full_path(attachment.store_fname)
        try:
            with open(file_path, 'rb') as file_obj:
                files = [('document', (attachment.name, file_obj, 'text/xml'))]
                response = requests.put(url, headers=headers, files=files, timeout=60)
        except OSError as err:
            raise UserError(_('Unable to read attachment file for %s: %s') % (attachment.display_name, err)) from err
        except requests.RequestException as err:
            raise UserError(_('Datapost submission request failed: %s') % err) from err

        invoice.ce_send_invoice_req_status = str(response.status_code)
        invoice.ce_send_invoice_content = response.text

        if response.status_code in (200, 202):
            invoice.ce_send_invoice_status = True
            invoice.ce_client_ref = str(client_ref)
        else:
            _logger.warning('CE InvoiceNow send failed for invoice %s: %s', invoice.id, response.text)

        return True

    def action_send_invoice(self):
        self.ensure_one()
        config = self.env['ce.invoice.now.configuration'].get_active_configuration()
        if not config:
            raise UserError(_('Please configure and activate CE InvoiceNow first.'))

        if self.move_type == 'out_invoice':
            document_type = config.inv_document_type
            document_format = config.inv_document_format
        else:
            document_type = config.credit_document_type
            document_format = config.credit_document_format

        for line in self.send_invoice_ids:
            attachment = self._resolve_xml_attachment(line.move_id, line.attachment_id, config)
            self._send_invoice_datapost(line.move_id, attachment, config, document_type, document_format)

        return {'type': 'ir.actions.act_window_close'}
