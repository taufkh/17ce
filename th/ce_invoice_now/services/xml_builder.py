# -*- coding: utf-8 -*-

import base64
import hashlib
import logging

from odoo import fields
from odoo.exceptions import UserError
from odoo.tools.translate import _

from .xml_mapper import CEInvoiceXMLMapper
from .xml_renderer import CEInvoiceXMLRenderer
from .xml_validator import CEInvoiceXMLValidator

_logger = logging.getLogger(__name__)


class CEInvoiceXMLBuilder:
    @classmethod
    def generate_for_invoice(cls, invoice, force=False):
        CEInvoiceXMLValidator.validate_invoice(invoice)

        payload = CEInvoiceXMLMapper.map_invoice(invoice)
        xml_bytes = CEInvoiceXMLRenderer.render(payload)
        CEInvoiceXMLValidator.validate_xml(xml_bytes)

        digest = hashlib.sha256(xml_bytes).hexdigest()
        if not force and invoice.ce_xml_hash and invoice.ce_xml_hash == digest and invoice.ce_xml_attachment_id:
            return invoice.ce_xml_attachment_id

        move_name = (invoice.name or f'move_{invoice.id}').replace('/', '_')
        attachment_name = f'{move_name}_ce.xml'
        attachment_vals = {
            'name': attachment_name,
            'type': 'binary',
            'datas': base64.b64encode(xml_bytes),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'mimetype': 'application/xml',
        }

        attachment = invoice.ce_xml_attachment_id
        if attachment:
            attachment.write(attachment_vals)
        else:
            attachment = invoice.env['ir.attachment'].create(attachment_vals)

        invoice.write(
            {
                'ce_xml_attachment_id': attachment.id,
                'ce_xml_generation_state': 'generated',
                'ce_xml_error_message': False,
                'ce_xml_generated_at': fields.Datetime.now(),
                'ce_xml_hash': digest,
            }
        )
        _logger.info('Generated CE XML for invoice %s (attachment %s)', invoice.id, attachment.id)
        return attachment

    @classmethod
    def generate_or_fail(cls, invoice, force=False):
        try:
            return cls.generate_for_invoice(invoice, force=force)
        except UserError as err:
            invoice.write(
                {
                    'ce_xml_generation_state': 'error',
                    'ce_xml_error_message': str(err),
                }
            )
            raise
        except Exception as err:  # pragma: no cover - defensive path
            invoice.write(
                {
                    'ce_xml_generation_state': 'error',
                    'ce_xml_error_message': str(err),
                }
            )
            raise UserError(_('Unexpected XML generation error: %s') % err) from err
